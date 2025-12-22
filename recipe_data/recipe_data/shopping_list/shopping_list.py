from recipe_data.recipe_data.list_blueprint.list_blueprint import ListBlueprint


class ShoppingList(ListBlueprint):
    def __init__(self):
        super().__init__("../data/fridge.json")
