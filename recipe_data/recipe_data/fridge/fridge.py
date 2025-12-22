from recipe_data.recipe_data.shopping_list.shopping_list import ListBlueprint


class Fridge(ListBlueprint):
    def __init__(self):
        super().__init__("../data/fridge.json")