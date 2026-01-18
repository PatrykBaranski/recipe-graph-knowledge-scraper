import os
from langchain_core.tools import Tool
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph, Neo4jVector
from langchain_openai import AzureOpenAIEmbeddings
from recipe_data.recipe_data.tools.common import llm
from recipe_data.recipe_data.tools.prompts import CYPHER_PROMPT, QA_PROMPT

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
            description="""OBOWIĄZKOWE narzędzie do wyszukiwania przepisów! Użyj ZAWSZE gdy użytkownik pyta o:
- przepisy na śniadanie/obiad/kolację
- co ugotować ze składników
- dania z określonymi składnikami
- przepisy na konkretne okazje
Przekaż pytanie w języku naturalnym, np. 'przepisy na śniadanie z jajkami i mlekiem' lub 'przepisy z kurczakiem'."""
        )
    except Exception as e:
        print(f"Failed to initialize GraphRAG: {e}")
        return None

def get_vector_rag_tool():
    api_key = os.getenv("AZURE_EMBEDDING_API_KEY")
    api_version = os.getenv("AZURE_EMBEDDING_API_VERSIONS")
    azure_endpoint = os.getenv("AZURE_EMBEDDING_ENDPOINT")
    model = os.getenv("AZURE_EMBEDDING_MODEL")

    embeddings = AzureOpenAIEmbeddings(api_key=api_key, api_version=api_version, model=model, 
                                       azure_endpoint=azure_endpoint) 
    
    vector_index = Neo4jVector.from_existing_graph(
        embeddings,
        url="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_PASSWORD", "DATABASE_PASSWORD"),
        index_name="recipes_vector",
        node_label="Recipe",
        text_node_properties=["title", "slug", "url"],
        embedding_node_property="embedding",
    )
    
    def search(query):
        results = vector_index.similarity_search(query)
        return "\n".join([doc.page_content for doc in results])

    return Tool(
        name="VectorRAG",
        func=search,
        description="""OBOWIĄZKOWE narzędzie do wyszukiwania przepisów! Użyj ZAWSZE gdy użytkownik pyta o:
- przepisy na śniadanie/obiad/kolację
- co ugotować ze składników
- dania z określonymi składnikami
Przekaż pytanie w języku naturalnym, np. 'przepisy na śniadanie' lub 'dania z kurczakiem'."""
    )
