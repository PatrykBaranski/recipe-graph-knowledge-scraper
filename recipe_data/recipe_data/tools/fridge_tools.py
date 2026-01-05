import json
from langchain_core.tools import tool
from recipe_data.recipe_data.tools.common import llm, fridge
from recipe_data.recipe_data.tools.prompts import conversion_prompt

@tool
def read_fridge() -> str:
    """
    Zwraca listę składaników z lodówki.

    Args:
    """
    return json.dumps(fridge.content, ensure_ascii=False)

@tool
def add_ingredient_to_fridge(ingredient_to_add: str, quantity: int, unit: str, category:str):
    """
    Dodaje nowy składnik do listy składników

    Args:
        ingredient_to_add: nazwa skłądnika, który ma zostać dodany.
        quantity: ilość składnika do dodania, jeżeli jest pusta, to ustaw tę wartość na jeden
        unit: jednostka w jakiej wystepuje dany składnik
        category: kategoria produktu (np. Nabiał, Warzywa, Owoce). Domyślnie 'Inne'.
    """
    data = {
        "ingredient": ingredient_to_add,
        "quantity": quantity,
        "unit": unit,
        "category": category
    }
    fridge.add_to_content(data)

@tool
def remove_ingredient_from_fridge(ingredient_to_remove: str, quantity: int, unit:str):
    """
    Usuwa składnik z listy składników

    Args:
        ingredient_to_remove: nazwa skłądnika, który ma zostać usunięty.
        quantity: ilość składnika do dodania, jeżeli jest pusta, to ustaw tę wartość na jeden
        unit: jednostka w jakiej występuje dany składnik.
    """
    data = {
        "ingredient": ingredient_to_remove,
        "quantity": quantity,
        "unit": unit,
    }
    fridge.remove_from_content(data)
