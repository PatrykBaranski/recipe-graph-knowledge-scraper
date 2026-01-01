import json
import os

from dotenv import load_dotenv
from langchain_classic import hub
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.tools import tool, Tool
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector

from recipe_data.recipe_data.fridge.fridge import Fridge
from recipe_data.recipe_data.shopping_list.shopping_list import ShoppingList

load_dotenv(override=True)
llm = AzureChatOpenAI(model="gpt-5-nano")
fridge = Fridge()
shopping_list = ShoppingList()
conversion_prompt = ChatPromptTemplate.from_template("""{question}
    To jest nazwa składnika wraz z jego ilością. Twoim zadaniem jest skategoryzowanie tego składnika, 
    czyli dodasz kategorię z jakiej on pochodzi i ich ilości, 
    jeżeli nie ma przy składniku liczby sugerującej ilość, to domyślnie ustaw 1 
    i zwrócenie ich w formacie json. 
    Nie dodawaj żadnego dodatkowego tekstu w odpowiedzi, sam czysty json, żeby móc go sformatować. 
    Dodatkowo do kluczy w odpowiedzi json użyj angielskich nazw: ingredient, category, quantity,
    """)


prompt = ChatPromptTemplate.from_messages([
    ("system", "Jesteś asystentem kulinarnym. Twoim zadaniem jest pomaganie użytkownikowi w zarządzaniu lodówką i znajdowaniu przepisów. "
               "Masz dostęp do narzędzi: read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge, add_ingredient_to_shopping_list, add_missing_ingredients_for_recipe oraz GraphRAG/VectorRAG. "
               "Jeśli używasz narzędzia GraphRAG do szukania przepisów, ZAWSZE zwracaj użytkownikowi dokładnie to, co zwróciło narzędzie. "
               "Nie wymyślaj własnych przepisów, jeśli narzędzie zwróciło listę. "
               "Jeśli narzędzie zwróciło przepisy, które są deserami, a użytkownik pytał o kolację, i tak je pokaż, zaznaczając, że to jest to co znaleziono w bazie. "
               "Jeśli użytkownik chce przygotować konkretne danie, użyj narzędzia add_missing_ingredients_for_recipe, aby dodać brakujące produkty do listy zakupów."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

@tool
def read_fridge() -> str:
    """
    Zwraca listę składaników z lodówki.

    Args:
    """
    function_prompt = ChatPromptTemplate.from_template("""
    To jest zawartość lodówki w formacie json: {question}, wylistuj nazwy skłądników (klucz ingredient) i ich ilość (quantity)
    """
                                              )
    response2 = llm.invoke(function_prompt.format(question=fridge.content))
    return response2.content

@tool
def add_ingredient_to_fridge(ingredient_to_add: str, quantity: int):
    """
    Dodaje nowy składnik do listy składników

    Args:
        ingredient_to_add: nazwa skłądnika, który ma zostać dodany.
        quantity: ilość składnika do dodania, jeżeli jest pusta, to ustaw tę wartość na jeden
    """

    function_response = llm.invoke(conversion_prompt.format(question=f"{ingredient_to_add, quantity}"))
    data = json.loads(function_response.content.replace("`", "").replace("\n", "").replace("json", "").strip(), strict=False)
    fridge.add_to_content(data)

@tool
def remove_ingredient_from_fridge(ingredient_to_remove: str, quantity: int):
    """
    Usuwa składnik z listy składników

    Args:
        ingredient_to_remove: nazwa skłądnika, który ma zostać usunięty.
        quantity: ilość składnika do dodania, jeżeli jest pusta, to ustaw tę wartość na jeden
    """
    function_response = llm.invoke(conversion_prompt.format(question=f"{ingredient_to_remove, quantity}"))
    data = json.loads(function_response.content.replace("`", "").replace("\n", "").replace("json", "").strip(), strict=False)
    fridge.remove_from_content(data)

@tool
def add_ingredient_to_shopping_list(ingredient_to_add: str, quantity: int):
    """
    Dodaje nowy składnik do listy zakupów.
    
    Args:
        ingredient_to_add: nazwa składnika, który ma zostać dodany.
        quantity: ilość składnika do dodania, jeżeli jest pusta, to ustaw tę wartość na jeden
    """
    function_response = llm.invoke(conversion_prompt.format(question=f"{ingredient_to_add, quantity}"))
    data = json.loads(function_response.content.replace("`", "").replace("\n", "").replace("json", "").strip(), strict=False)
    shopping_list.add_to_content(data)
    return "Added to shopping list"

@tool
def add_missing_ingredients_for_recipe(recipe_title: str):
    """
    Dodaje brakujące składniki dla wybranego przepisu do listy zakupów.
    Użyj tego narzędzia, gdy użytkownik wyraźnie poprosi o dodanie składników na konkretne danie do listy zakupów.
    
    Args:
        recipe_title: Tytuł przepisu, dla którego mają zostać dodane składniki.
    """
    try:
        graph = get_neo4j_graph()
        
        # Wyszukaj przepis (case-insensitive)
        query = """
        MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
        WHERE r.title =~ $title
        RETURN r.title as title, collect(i.name) as ingredients
        """
        # (?i) flag for case-insensitive in Neo4j regex
        result = graph.query(query, {"title": f"(?i).*{recipe_title}.*"})
        
        if not result:
            return f"Nie znaleziono przepisu pasującego do nazwy: {recipe_title}"
        
        # Bierzemy pierwszy pasujący przepis
        found_title = result[0]['title']
        recipe_ingredients = result[0]['ingredients']
        
        # Pobierz aktualny stan lodówki
        current_fridge = fridge.content 
        if not current_fridge:
            current_fridge = []
            
        fridge_items = {item.get('ingredient', '').lower() for item in current_fridge}
        
        missing_items = []
        for ing in recipe_ingredients:
            if ing.lower() not in fridge_items:
                missing_items.append(ing)
        
        if not missing_items:
            return f"Masz wszystkie składniki na {found_title}!"
            
        # Dodaj brakujące do listy zakupów
        for item in missing_items:
            shopping_list.add_to_content({
                "ingredient": item,
                "quantity": 1,
                "category": "Brakujące do: " + found_title
            })
            
        return f"Dodano do listy zakupów {len(missing_items)} brakujących składników na {found_title}: {', '.join(missing_items)}"
        
    except Exception as e:
        return f"Błąd podczas przetwarzania: {e}"

base_tools = [read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge, add_ingredient_to_shopping_list, add_missing_ingredients_for_recipe]

CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}

Examples:
# Find recipes containing 'jajka'
MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient) WHERE i.name CONTAINS 'jajka' RETURN r.title, r.url

# Find recipes suitable for 'obiad'
MATCH (r:Recipe)-[:PERFECT_FOR]->(o:Occasion) WHERE o.name CONTAINS 'obiad' RETURN r.title, r.url

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

When searching for recipes based on ingredients, always follow this pattern:
1. Match recipes that contain ANY of the provided ingredients.
2. If the question mentions 'śniadanie', 'obiad', or 'kolacja', filter recipes by matching (r)-[:PERFECT_FOR]->(o:Occasion) where o.name matches the meal type (case-insensitive).
3. For each recipe, calculate the number of matching ingredients.
4. Also find which ingredients from the recipe are MISSING from the provided list.
5. Order by the number of matching ingredients DESCENDING.
6. Return the recipe title, url, matching count, and the list of missing ingredients.

The question is:
{question}"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

QA_GENERATION_TEMPLATE = """Jesteś asystentem kulinarnym.
Oto wyniki wyszukiwania przepisów z bazy danych (Context):
{context}

Pytanie użytkownika:
{question}

Twoim zadaniem jest przedstawienie użytkownikowi znalezionych przepisów.
Wymień WSZYSTKIE przepisy z sekcji Context.
Dla każdego przepisu podaj: Tytuł, Link, Liczbę pasujących składników oraz Brakujące składniki.
Nie filtruj wyników. Nie oceniaj czy pasują do zapytania (np. czy to kolacja).
Nie dodawaj komentarzy typu "Niestety żaden przepis nie pasuje".
Po prostu przekaż znalezione dane w czytelnej formie listy.

Jeśli Context jest pusty, napisz: "Nie znaleziono przepisów w bazie danych."
"""

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_GENERATION_TEMPLATE
)

def get_neo4j_graph():
    graph = Neo4jGraph(
        url="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_PASSWORD", "DATABASE_PASSWORD")
    )
    graph.refresh_schema()
    return graph

def get_graph_rag_tool():
    try:
        graph = get_neo4j_graph()
        print(f"Neo4j Schema: {graph.schema}")
        chain = GraphCypherQAChain.from_llm(
            llm, 
            graph=graph, 
            verbose=True, 
            allow_dangerous_requests=True,
            cypher_prompt=CYPHER_PROMPT,
            qa_prompt=QA_PROMPT
        )
        return Tool(
            name="GraphRAG",
            func=chain.run,
            description="Użyj tego narzędzia, aby wyszukać przepisy w bazie danych grafowych Neo4j. Zadawaj pytania w języku naturalnym."
        )
    except Exception as e:
        print(f"Failed to initialize GraphRAG: {e}")
        return None

def get_vector_rag_tool():
    # Assuming embeddings are configured in env
    embeddings = AzureOpenAIEmbeddings() 
    
    vector_index = Neo4jVector.from_existing_graph(
        embeddings,
        url="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_PASSWORD", "DATABASE_PASSWORD"),
        index_name="recipes_vector",
        node_label="Recipe",
        text_node_properties=["title", "slug"],
        embedding_node_property="embedding",
    )
    
    def search(query):
        results = vector_index.similarity_search(query)
        return "\n".join([doc.page_content for doc in results])

    return Tool(
        name="VectorRAG",
        func=search,
        description="Użyj tego narzędzia, aby wyszukać przepisy używając wyszukiwania wektorowego (podobieństwo tekstu)."
    )

class FridgeChatbot:
    def __init__(self, tools=None):
        self.tools = tools if tools else base_tools
        agent = create_tool_calling_agent(llm, self.tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        self.chat_history = []

    def chat(self, message: str) -> str:
        result = self.agent_executor.invoke({
            "input": message,
            "chat_history": self.chat_history
        })
        self.chat_history.extend([HumanMessage(content=message), AIMessage(content=result["output"])])
        return result["output"]

    def update_tools(self, use_neo4j=False, rag_type="Graph RAG"):
        current_tools = base_tools.copy()
        if use_neo4j:
            if rag_type == "Graph RAG":
                tool = get_graph_rag_tool()
                if tool:
                    current_tools.append(tool)
            elif rag_type == "RAG":
                tool = get_vector_rag_tool()
                if tool:
                    current_tools.append(tool)
        
        print(f"Active tools: {[t.name for t in current_tools]}")
        self.tools = current_tools
        agent = create_tool_calling_agent(llm, self.tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    def clear_history(self):
        self.chat_history = []


agent = create_tool_calling_agent(llm, base_tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=base_tools, verbose=True)


if __name__ == "__main__":
    ## Przykładowe użycie
    fridge_chatbot = FridgeChatbot()
    response = fridge_chatbot.chat("Jakie składniki są w lodówce?")
    print(response)
