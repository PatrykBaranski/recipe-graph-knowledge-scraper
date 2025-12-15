import json
import os


class Fridge:

    filename = "../data/fridge.json"

    def __init__(self):
        self.fridge_content = self.load_fridge()

    def load_fridge(self):
        if os.path.isfile(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        else:
            self.save_fridge([])
            return []

    def save_fridge(self, full_fridge_json):
        json_str = json.dumps(full_fridge_json, indent=4)
        with open(self.filename, "w") as f:
            f.write(json_str)

    def add_to_fridge(self, ingredient_to_add):
        found = False
        for ingredient in self.fridge_content:
            if ingredient["ingredient"] == ingredient_to_add["ingredient"]:
                ingredient["quantity"] += ingredient_to_add["quantity"]
                found = True
                break
        if not found:
            self.fridge_content.append(ingredient_to_add)
        self.save_fridge(self.fridge_content)

    def remove_from_fridge(self, thing_to_remove):
        found = False
        for ingredient in self.fridge_content:
            if ingredient["ingredient"] == thing_to_remove["ingredient"]:
                if ingredient["quantity"] < thing_to_remove["quantity"]:
                    self.fridge_content.remove(thing_to_remove)
                else:
                    ingredient["quantity"] -= thing_to_remove["quantity"]
                found = True
                break
        if not found:
            print("Nie znaleziono składnika")

        self.save_fridge(self.fridge_content)