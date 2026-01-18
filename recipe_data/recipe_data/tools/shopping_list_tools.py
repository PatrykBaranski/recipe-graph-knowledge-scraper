import json
from langchain_core.tools import tool
from recipe_data.recipe_data.tools.common import llm, shopping_list, fridge
from recipe_data.recipe_data.tools.prompts import conversion_prompt
from recipe_data.recipe_data.tools.rag_tools import get_neo4j_graph

@tool
def read_shopping_list() -> str:
    """
    Zwraca listę produktów z LISTY ZAKUPÓW - czyli rzeczy które użytkownik MUSI KUPIĆ.
    Użyj tego narzędzia TYLKO gdy użytkownik pyta o listę zakupów, co musi kupić, co jest na liście.
    NIE używaj tego do lodówki - do tego służy read_fridge.

    Returns:
        JSON z listą produktów do kupienia.
    """
    return json.dumps(shopping_list.content, ensure_ascii=False)

@tool
def add_ingredient_to_shopping_list(ingredient_to_add: str, quantity: int):
    """
    Dodaje nowy składnik do LISTY ZAKUPÓW - czyli do listy rzeczy, które użytkownik MUSI KUPIĆ.
    Użyj tego narzędzia gdy użytkownik chce dodać coś do zakupów, potrzebuje kupić produkt.
    NIE używaj tego do lodówki (produkty które już ma) - do tego służy add_ingredient_to_fridge.
    
    Args:
        ingredient_to_add: nazwa składnika do dodania na listę zakupów.
        quantity: ilość do kupienia (domyślnie 1 jeśli nie podano).
    """
    function_response = llm.invoke(conversion_prompt.format(question=f"{ingredient_to_add, quantity}"))
    data = json.loads(function_response.content.replace("`", "").replace("\n", "").replace("json", "").strip(), strict=False)
    shopping_list.add_to_content(data)
    return "Dodano do listy zakupów"

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
        
      
        query = """
        MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
        WHERE r.title =~ $title
        RETURN r.title as title, collect(i.name) as ingredients
        """
      
        result = graph.query(query, {"title": f"(?i).*{recipe_title}.*"})
        
        if not result:
            return f"Nie znaleziono przepisu pasującego do nazwy: {recipe_title}"
        
     
        found_title = result[0]['title']
        recipe_ingredients = result[0]['ingredients']
        
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

@tool
def create_shopping_list_file_for_recipe(recipe_title: str):
    """
    Tworzy plik tekstowy z listą brakujących składników dla wybranego przepisu.
    Użyj tego narzędzia, gdy użytkownik woli otrzymać plik zamiast dodawać składniki do wewnętrznej listy zakupów.
    
    Args:
        recipe_title: Tytuł przepisu, dla którego ma zostać wygenerowana lista.
    """
    try:
        graph = get_neo4j_graph()
        
        query = """
        MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
        WHERE r.title =~ $title
        RETURN r.title as title, collect(i.name) as ingredients
        """
      
        result = graph.query(query, {"title": f"(?i).*{recipe_title}.*"})
        
        if not result:
            return f"Nie znaleziono przepisu pasującego do nazwy: {recipe_title}"
        
       
        found_title = result[0]['title']
        recipe_ingredients = result[0]['ingredients']
        

        current_fridge = fridge.content 
        if not current_fridge:
            current_fridge = []
            
        fridge_items = {item.get('ingredient', '').lower() for item in current_fridge}
        
        missing_items = []
        for ing in recipe_ingredients:
            if ing.lower() not in fridge_items:
                missing_items.append(ing)
        
        if not missing_items:
            return f"Masz wszystkie składniki na {found_title}! Nie trzeba tworzyć listy."
            
    
        filename = f"lista_zakupow_{found_title.replace(' ', '_')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"Lista zakupów dla przepisu: {found_title}\n")
            f.write("="*30 + "\n")
            for item in missing_items:
                f.write(f"- [ ] {item}\n")
            
        return f"Stworzono plik z listą zakupów: {filename}. Zawiera {len(missing_items)} brakujących składników."
        
    except Exception as e:
        return f"Błąd podczas tworzenia pliku: {e}"
