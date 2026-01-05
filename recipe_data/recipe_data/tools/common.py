from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from recipe_data.recipe_data.fridge.fridge import Fridge
from recipe_data.recipe_data.shopping_list.shopping_list import ShoppingList

load_dotenv(override=True)
llm = AzureChatOpenAI(model="gpt-5-nano")
fridge = Fridge()
shopping_list = ShoppingList()
