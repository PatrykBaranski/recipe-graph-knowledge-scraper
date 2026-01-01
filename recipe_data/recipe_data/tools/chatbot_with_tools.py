import json
import os

from dotenv import load_dotenv
from langchain_classic import hub
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.tools import tool, Tool
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector

from recipe_data.recipe_data.fridge.fridge import Fridge

load_dotenv(override=True)
llm = AzureChatOpenAI(model="gpt-5-nano")
fridge = Fridge()
conversion_prompt = ChatPromptTemplate.from_template("""{question}
    To jest nazwa składnika wraz z jego ilością. Twoim zadaniem jest skategoryzowanie tego składnika, 
    czyli dodasz kategorię z jakiej on pochodzi i ich ilości, 
    jeżeli nie ma przy składniku liczby sugerującej ilość, to domyślnie ustaw 1 
    i zwrócenie ich w formacie json. 
    Nie dodawaj żadnego dodatkowego tekstu w odpowiedzi, sam czysty json, żeby móc go sformatować. 
    Dodatkowo do kluczy w odpowiedzi json użyj angielskich nazw: ingredient, category, quantity,
    """)


prompt = hub.pull("hwchase17/openai-tools-agent")

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

base_tools = [read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge]

def get_neo4j_graph():
    return Neo4jGraph(
        url="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_PASSWORD", "DATABASE_PASSWORD")
    )

def get_graph_rag_tool():
    try:
        graph = get_neo4j_graph()
        chain = GraphCypherQAChain.from_llm(
            llm, graph=graph, verbose=True, allow_dangerous_requests=True
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
    try:
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
    except Exception as e:
        print(f"Failed to initialize VectorRAG: {e}")
        return None

class FridgeChatbot:
    def __init__(self, tools=None):
        self.tools = tools if tools else base_tools
        agent = create_tool_calling_agent(llm, self.tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def chat(self, message: str) -> str:
        result = self.agent_executor.invoke({"input": message})
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
        
        self.tools = current_tools
        agent = create_tool_calling_agent(llm, self.tools, prompt=prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)


agent = create_tool_calling_agent(llm, base_tools, prompt=prompt)
agent_executor = AgentExecutor(agent=agent, tools=base_tools, verbose=True)


if __name__ == "__main__":
    ## Przykładowe użycie
    fridge_chatbot = FridgeChatbot()
    response = fridge_chatbot.chat("Jakie składniki są w lodówce?")
    print(response)
