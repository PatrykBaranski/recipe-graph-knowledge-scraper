from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

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
               "Masz dostęp do narzędzi: read_fridge, add_ingredient_to_fridge, remove_ingredient_from_fridge, add_ingredient_to_shopping_list, add_missing_ingredients_for_recipe, create_shopping_list_file_for_recipe oraz GraphRAG/VectorRAG. "
               "Jeśli używasz narzędzia GraphRAG do szukania przepisów, ZAWSZE zwracaj użytkownikowi dokładnie to, co zwróciło narzędzie. "
               "Nie wymyślaj własnych przepisów, jeśli narzędzie zwróciło listę. "
               "Jeśli narzędzie zwróciło przepisy, które są deserami, a użytkownik pytał o kolację, i tak je pokaż, zaznaczając, że to jest to co znaleziono w bazie. "
               "Gdy użytkownik wybierze konkretne danie, NIE dodawaj automatycznie składników do listy zakupów. "
               "Zamiast tego, ZAPROPONUJ użytkownikowi dwie opcje: "
               "1. Dodanie brakujących składników do Twojej wewnętrznej listy zakupów (użyj narzędzia add_missing_ingredients_for_recipe TYLKO po wyraźnej zgodzie). "
               "2. Wygenerowanie pliku z listą zakupów (np. notatka), który może sobie zapisać (użyj narzędzia create_shopping_list_file_for_recipe). "
               "Czekaj na decyzję użytkownika przed wykonaniem akcji."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

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

# Find recipes with ingredients 'jajka' and 'mleko', calculate missing ingredients
MATCH (r:Recipe)-[:CONTAINS]->(i:Ingredient)
WITH r, collect(i.name) AS recipe_ingredients
WITH r, recipe_ingredients, [ing IN recipe_ingredients WHERE ing IN ['jajka', 'mleko']] AS matching_ingredients
WITH r, recipe_ingredients, size(matching_ingredients) AS match_count
WHERE match_count > 0
RETURN r.title, r.url, match_count, [ing IN recipe_ingredients WHERE NOT ing IN ['jajka', 'mleko']] AS missing_ingredients
ORDER BY match_count DESC

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

When searching for recipes based on ingredients, always follow this pattern:
1. Identify the ingredients provided in the question.
2. Match recipes that contain ANY of the provided ingredients.
3. If the question mentions 'śniadanie', 'obiad', or 'kolacja', filter recipes by matching (r)-[:PERFECT_FOR]->(o:Occasion) where o.name matches the meal type (case-insensitive).
4. For each recipe, calculate the number of matching ingredients.
5. Also find which ingredients from the recipe are MISSING from the provided list.
6. Order by the number of matching ingredients DESCENDING.
7. Return the recipe title, url, matching count, and the list of missing ingredients.

The question is:
{question}"""

CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

QA_GENERATION_TEMPLATE = """Jesteś asystentem kulinarnym.
Oto wyniki wyszukiwania przepisów z bazy danych (Context). Wyniki zawierają tytuł, link, liczbę pasujących składników oraz listę brakujących składników zwróconą przez bazę danych.
Context:
{context}

Pytanie użytkownika:
{question}

Twoim zadaniem jest przedstawienie użytkownikowi znalezionych przepisów.
Wymień WSZYSTKIE przepisy z sekcji Context.
Dla każdego przepisu podaj: Tytuł, Link, Liczbę pasujących składników oraz Brakujące składniki.

WAŻNE:
- Listę "Brakujące składniki" przepisz DOKŁADNIE tak, jak została zwrócona w Context.
- NIE wymyślaj ani nie zgaduj brakujących składników. Jeśli lista w Context jest pusta, napisz "brak".
- Nie filtruj wyników. Nie oceniaj czy pasują do zapytania (np. czy to kolacja).
- Nie dodawaj komentarzy typu "Niestety żaden przepis nie pasuje".
- Po prostu przekaż znalezione dane w czytelnej formie listy.

Jeśli Context jest pusty, napisz: "Nie znaleziono przepisów w bazie danych."
"""

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_GENERATION_TEMPLATE
)
