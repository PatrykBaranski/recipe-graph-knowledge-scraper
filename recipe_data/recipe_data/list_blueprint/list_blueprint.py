import json
import os


class ListBlueprint:
    def __init__(self, filename):
        self.filename = filename
        self.content = self.load_content()

    def load_content(self):
        if os.path.isfile(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        else:
            self.save_content([])
            return []

    def save_content(self, full_fridge_json):
        json_str = json.dumps(full_fridge_json, indent=4)
        with open(self.filename, "w") as f:
            f.write(json_str)

    def add_to_content(self, ingredient_to_add):
        found = False
        for ingredient in self.content:
            if ingredient["ingredient"] == ingredient_to_add["ingredient"] and ingredient.get("unit") == ingredient_to_add.get("unit"):
                ingredient["quantity"] += ingredient_to_add["quantity"]
                found = True
                break
        if not found:
            self.content.append(ingredient_to_add)
        self.save_content(self.content)

    def remove_from_content(self, thing_to_remove):
        found = False
        for ingredient in self.content:
            if ingredient["ingredient"] == thing_to_remove["ingredient"] and ingredient.get("unit") == thing_to_remove.get("unit"):
                if ingredient["quantity"] <= thing_to_remove["quantity"]:
                    self.content.remove(ingredient)
                else:
                    ingredient["quantity"] -= thing_to_remove["quantity"]
                found = True
                break
        if not found:
            print("Nie znaleziono składnika")

        self.save_content(self.content)