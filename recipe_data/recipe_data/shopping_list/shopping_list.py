from recipe_data.recipe_data.list_blueprint.list_blueprint import ListBlueprint
import os


class ShoppingList(ListBlueprint):
    def __init__(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_path, "data", "shopping_list.json")
        super().__init__(data_path)
