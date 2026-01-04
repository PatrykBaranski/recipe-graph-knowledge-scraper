from neo4j import GraphDatabase
from bs4 import BeautifulSoup

class RecipeDataPipeline:
    def __init__(self):

        self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", ""))

    def close_spider(self, spider):
        self.driver.close()

    def process_item(self, item, spider):
        with self.driver.session() as session:
            session.execute_write(self._save_recipe, item)
        return item

    @staticmethod
    def _save_recipe(tx, item):
        query_recipe = """
        MERGE (r:Recipe {slug: $slug})
        SET r.id = $id,
            r.title = $title,
            r.prep_time = $prep_time,
            r.yield_amount = $yield_amount,
            r.url = $url,
            r.last_updated = datetime()
        """
        tx.run(query_recipe, 
               id=item.get('id'), 
               slug=item.get('slug'), 
               title=item.get('title'),
               prep_time=item.get('recipePrepTime'),
               yield_amount=item.get('recipeYield'),
               url=f"https://aniagotuje.pl/przepis/{item.get('slug')}"
        )

        cuisine = item.get('recipeCuisine')
        if cuisine:
            query_cuisine = """
            MATCH (r:Recipe {slug: $slug})
            MERGE (c:Cuisine {name: $cuisine})
            MERGE (r)-[:BELONGS_TO]->(c)
            """
            tx.run(query_cuisine, slug=item.get('slug'), cuisine=cuisine)

        categories = item.get('categories', [])
        for cat in categories:
            cat_type = cat.get('type')
            cat_name = cat.get('name')
            
            if cat_type == 'DIET':
                query_diet = """
                MATCH (r:Recipe {slug: $slug})
                MERGE (d:Diet {name: $name})
                MERGE (r)-[:SUITABLE_FOR]->(d)
                """
                tx.run(query_diet, slug=item.get('slug'), name=cat_name)
            
            elif cat_type == 'IDEA': 
                query_occasion = """
                MATCH (r:Recipe {slug: $slug})
                MERGE (o:Occasion {name: $name})
                MERGE (r)-[:PERFECT_FOR]->(o)
                """
                tx.run(query_occasion, slug=item.get('slug'), name=cat_name)

        body_html = item.get('body', '')
        if body_html:
            soup = BeautifulSoup(body_html, 'html.parser')
            ingredients_div = soup.find('div', id='recipeIngredients')
            if ingredients_div:
                items = ingredients_div.select('li span[itemprop="recipeIngredient"]')
                for ing_span in items:
                    name_span = ing_span.find('span', class_='ingredient')
                    qty_span = ing_span.find('span', class_='qty')
                    
                    ing_name = name_span.get_text(strip=True) if name_span else None
                    ing_qty = qty_span.get_text(strip=True) if qty_span else ""
                    
                    if ing_name:
                        query_ing = """
                        MATCH (r:Recipe {slug: $slug})
                        MERGE (i:Ingredient {name: $name})
                        MERGE (r)-[rel:CONTAINS]->(i)
                        SET rel.quantity = $qty
                        """
                        tx.run(query_ing, slug=item.get('slug'), name=ing_name, qty=ing_qty)
