import json
from langchain_core.tools import tool
from recipe_data.recipe_data.tools.common import llm, fridge
from recipe_data.recipe_data.tools.prompts import conversion_prompt

@tool
def read_fridge() -> str:
    """
    Zwraca listę składników znajdujących się w LODÓWCE użytkownika.
    Użyj tego narzędzia TYLKO gdy użytkownik pyta o zawartość lodówki (co ma w domu, jakie produkty posiada).
    NIE używaj tego do listy zakupów - do tego służy osobne narzędzie.

    Returns:
        JSON z listą składników w lodówce.
    """
    return json.dumps(fridge.content, ensure_ascii=False)

@tool
def add_ingredient_to_fridge(ingredient_to_add: str, quantity: int, unit: str, category:str):
    """
    Dodaje nowy składnik do LODÓWKI użytkownika - czyli do listy produktów, które użytkownik JUŻ POSIADA w domu.
    Użyj tego narzędzia gdy użytkownik mówi że kupił coś, ma coś w domu, lub chce dodać produkt do lodówki.
    NIE używaj tego do listy zakupów (rzeczy do kupienia) - do tego służy add_ingredient_to_shopping_list.

    Args:
        ingredient_to_add: nazwa składnika, który ma zostać dodany do lodówki.
        quantity: ilość składnika (domyślnie 1 jeśli nie podano).
        unit: jednostka (np. szt, kg, g, l, ml).
        category: kategoria produktu (np. Nabiał, Warzywa, Owoce, Mięso). Domyślnie 'Inne'.
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
    Usuwa składnik z LODÓWKI użytkownika - czyli z listy produktów, które użytkownik posiada w domu.
    Użyj tego narzędzia gdy użytkownik zużył produkt, wyrzucił go, lub chce usunąć coś z lodówki.
    NIE używaj tego do listy zakupów.

    Args:
        ingredient_to_remove: nazwa składnika do usunięcia z lodówki.
        quantity: ilość do usunięcia (domyślnie 1 jeśli nie podano).
        unit: jednostka w jakiej występuje dany składnik.
    """
    data = {
        "ingredient": ingredient_to_remove,
        "quantity": quantity,
        "unit": unit,
    }
    fridge.remove_from_content(data)
