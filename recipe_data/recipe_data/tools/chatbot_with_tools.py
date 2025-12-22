import json
import string

from dotenv import load_dotenv
from langchain_classic import hub
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool

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
        ingredient_to_remove: nazwa skłądnika, który ma zostać dodany.
        quantity: ilość składnika do dodania, jeżeli jest pusta, to ustaw tę wartość na jeden
    """
    function_response = llm.invoke(conversion_prompt.format(question=f"{ingredient_to_remove, quantity}"))
    data = json.loads(function_response.content.replace("`", "").replace("\n", "").replace("json", "").strip(), strict=False)
    fridge.remove_from_content(data)

tools = [read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge]

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# result = agent_executor.invoke({"input": "Dodaj ketchup do lodówki"})
# print(f"Agent result: {result['output']}")

class FridgeChatbot:
    def __init__(self, fridge_agent_executor: AgentExecutor):
        self.agent_executor = fridge_agent_executor

    def chat(self, message: str) -> str:
        result = self.agent_executor.invoke({"input": message})
        return result["output"]

## Przykładowe użycie
fridge_chatbot = FridgeChatbot(agent_executor)
response = fridge_chatbot.chat("Jakie składniki są w lodówce?")
print(response)
