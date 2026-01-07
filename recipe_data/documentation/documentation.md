1. Wprowadzenie
<br><strong>Problem biznesowy</strong>: Agent asystujący przy planowaniu posiłków. 
Ma wyszukiwać przepisy na podstawie tego co użytknownik ma w lodówce, 
tworzyć listy zakupów na podstawie przepisów, które użytkownik chce wykonać.
<br><strong>Użyte technolgie</strong>: Neo4j, 
Langchain, Tavily, Azure Cognitive Services
2. Opis modułów
<br>**Przechowywanie danych**:
Dane *lodówki* i *listy zakupów* przechowywane są lokalnie w 
folderze: **data** w formacie `json`. 
Zarządzanie nimi(*odczyt, zapis, dodawanie, usuwanie*) odbywa się za pomocą klasy 
`ListBlueprint`, która jest implementowana jest odpowiednio przez przez klasy: `Fridge` i `ShoppingList`.
<br>**Odczyt danych z pisma ręcznego**:
System pozwala na odczyt danych z pisma ręcznego. 
Zajmuje się tym klasa: `PhotoReader`. Zdjęcie jest odczytywane w postaci *bajtów*, 
następnie jest analizowane przez `ImageAnalysisClient`. 
Dane odczytane przez klienta zostają odpowiednio 
przetworzone przez llm (w tym projekcie użyto:
**gpt-5-nano**), oraz zwrócone jako `json`.
<br>**Zaciąganie danych ze strony AniaGotuje**: 
Dane ze strony aniagotuje.pl są zaciągane 
za pomocą **scrapera**`AniaGotujeSpider`(startując z url: 
*https://api.aniagotuje.pl/client/posts/search?perPage=200&page=0&sort=publish,desc*)
i dodawane w ustrukturyzowanej formie za pomocą `RecipeDataPipeline`.
<br>**Agent**: Za zarządzanie systemem i przetwarzanie zapytań użytkownika 
odpowiada **Agent(`FridgeChatbot`)**, znajdujący się 
w pliku **chatbot_with_tools.py**. Prompty znajdują się w pliku 
**fridge_tools.py** i **shopping_list_tools**. 
Konfiguracje **RAG** i **Graph RAG** znajdują się w **rag_tools.py**.
<br>**Front**: Front został wykonany w **streamlit** i 
znajduje się w pliku **app.py**. Jest prosty i czytelny, na samym początku użytkownika
wida pole tekstowe zachęcające do rozpoczęcia integracji z asystentem, po prawej stronie
widoczne jest podsumowanie co użytkownik ma odpowiednio w *Lodówce* i na *Liście zakupów*, a
z prawej znajduje się lista wyboru widoku: *Chatbot*, *Lodówka*, *Lista zakupów*, oraz
lista z wyborem opcji. Wybranie opcji *Neo4j* pozwala na dalszy wybór: *RAG*,
albo *Graph RAG*.
<br>**Toole**:
- `read_fridge` -> Zwraca listę składaników z lodówki
- `add_ingredient_to_fridge` -> Dodaje nowy składnik do 
listy składników w lodówce
- `remove_ingredient_from_fridge` -> Usuwa składnik z
listy składników w lodówce
- `add_ingredient_to_shopping_list` -> Dodaje nowy składnik do 
listy zakupów
- `add_missing_ingredients_for_recipe` -> Dodaje do listy
zakupów produkty potrzebne do wykonania przepisu, których
nie ma w lodówce. Używany, gdy użytkownik wyraźnie o to 
poprosi
- `create_shopping_list_file_for_recipe` -> Zwraca listę brakujacych składników,
gdy użytkownik nie chce dodawać tych składników do listy
3. Knowledge Graph
<br>**Przykładowy fragment grafu**:![sample](sample_graph.png)
Każdy **przepis** ma relację: *CONTAINS* 
ze składnikami, które go tworzą, *BELONGS_TO* z rodzajem
kuchni do której należy(np. polska, włoska itp),
*SUITABLE_FOR* dla rodzaju diety (np. bezglutenowa).
Pozwala to na dokładne wyszukiwanie przepisów w zależnosći
od preferencji użytkownika i od składników, które ma,
bądź chce użyć.
4. Zaawansowane zapytania
<br>**Przykładowa konwersacja z chatbotem**:
![sample_chat](sample1.png)
![sample_chat](sample2.png)
![sample_chat](sample3.png)
![sample_chat](sample4.png)
5. Metryki
<br>

| Pytanie                  | 	Odpowiedź RAG                                                                                                                                                         | Odpowiedź Graph RAG	                                                                                                                                                                                                   | Czas RAG | Czas Graph RAG |
|:-------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| :---------| :-----|
| Ile jajek mam w lodówce? | Masz 6 jajek w lodówce.                                                                                                                                                | Masz 6 jajek w lodówce.                                                                                                                                                                                                | 00:01,55 | 00:03,08 |
| Co mogę zrobić na śniadanie z jajek? | "Podał 4 proste przepisy (Jajecznicza, omlet, jajka sadzone, Frittata) i zapytał: Chcesz dodać brakujące składniki do listy  zakupów, czy potrzebujesz pliku z listą?" | "Przedstawił 10 propozycji przepisów z linkami i komunikat: Jeżeli któryś przepis Cię interesuje, chętnie pomogę w dodaniu brakujących składników do listy zakupów lub przygotuję plik z listą składników! Co wolisz?" | 00:12,25 | 00:16,62 |

O ile zwykły RAG działa ciutkę szybicej, to GraphRag nadrabia różnorodnością, podając linki do przepisów,
a nie tylko ich skróconą formę, oraz podaje ich znacznie więcej.
6. Wnioski i rekomendacje
7. Załączniki
<br>**Miejsce przechowywania projektu:**
[Repozytorium na GitHub](https://github.com/PatrykBaranski/recipe-graph-knowledge-scraper)
<br>**Konfiguracja:**
<br>
   1. Wszystkie potrzebne paczki znajdują się w pliku: **requirements.txt**, 
   należy je pobrać.
   2. Stworzyć kontener z **neo4j**
      1. Pobrać obraz **neo4j**
      2. Wywołać komendę: <br>`docker run \
    -p 7474:7474 -p 7687:7687 \
    -v $PWD/data:/data -v $PWD/plugins:/plugins \
    --name neo4j-apoc \
    -e NEO4J_apoc_export_file_enabled=true \
    -e NEO4J_apoc_import_file_enabled=true \
    -e NEO4J_apoc_import_file_use__neo4j__config=true \
    -e NEO4JLABS_PLUGINS=\[\"apoc\"\] \
    neo4j`
   3. Wywołać komendę: `.venv/bin/activate `, 
   żeby aktywować środowisko wirtualne
   4. Przygotować plik: **.env**, 
   żeby posiadał następujące dane:
   <br>`AZURE_OPENAI_ENDPOINT="https://s20519.openai.azure.com/openai/deployments/gpt-4o-mini/chat/completions?api-version=2025-01-01-preview"
AZURE_OPENAI_API_KEY=""
OPENAI_API_VERSION="2025-01-01-preview"
TAVILY_API_KEY=""
COGNITIVE_API="https://fridgepoc.cognitiveservices.azure.com/"
COGNITIVE_KEY=""
NEO4J_PASSWORD=""` (*klucze i hasło do **neo4j** należy wypełnić swoimi danymi*)
   5. Urchomić scraper komendą: `scrapy crawl aniagotuje_spider`
   6. Uruchomić aplikację komendą: `streamlit run app.py `