from recipe_data.recipe_data.shopping_list.shopping_list import ListBlueprint
import os


class Fridge(ListBlueprint):
    def __init__(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_path, "data", "fridge.json")
        super().__init__(data_path)