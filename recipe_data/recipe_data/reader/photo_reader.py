import json
import os
from xml.etree.ElementTree import indent

from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI


def load_image_from_path_as_bytes(photo_path):
    with open(photo_path, "rb") as f:
        return  f.read()


class PhotoReader:

    try:
        load_dotenv(override=True)
        endpoint = os.getenv("COGNITIVE_API")
        key = os.getenv("COGNITIVE_KEY")
    except KeyError:
        print("Missing environment variable 'VISION_ENDPOINT' or 'VISION_KEY'")
        print("Set them before running this sample.")
        exit()

    client = ImageAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    prompt = ChatPromptTemplate.from_template("""Jesteś asystentem do planowania posiłków i wyszukiwania odpowiednich przepisów.
                                              Dostaniesz listę zakupów, Twoim zadaniem jest pozbycie się tekstu, 
                                              który nie jest produktem spożywczym, następnie
                                              skategoryzowanie produktów, czyli dodasz kategorię z jakiej on pochodzi i ich ilości, 
                                              jeżeli nie ma przy składniku liczby sugerującej ilość, to domyślnie ustaw 1 
                                              i zwrócenie ich w formacie json. 
                                              Nie dodawaj żadnego dodatkowego tekstu w odpowiedzi, sam czysty json, żeby móc go sformatować. 
                                              Dodatkowo do kluczy w odpowiedzi json użyj angielskich nazw: ingredient, category, quantity, unit.
                                              Quantity powinno być liczbą (integer lub float). Unit powinno być jednostką (np. kg, g, l, szt, opakowanie). Jeśli brak jednostki, użyj "szt".

                                              Oto Twoja lista zakupów: {question}""")

    def get_list_from_photo_path(self, photo_path):
        llm = AzureChatOpenAI(model="gpt-5-nano")

        result = self.client.analyze(
            image_data=load_image_from_path_as_bytes(photo_path),
            visual_features=[VisualFeatures.READ],
        )

        response = llm.invoke(self.prompt.format(question=result.read.blocks[0].lines))
        data = json.loads(response.content.replace("`", "").replace("\n", "").replace("json", "").strip(), strict=False)
        return data


if __name__ == "__main__":
    ## Testing purpose
    test = PhotoReader()
    test2 = test.get_list_from_photo_path("shopping_list.jpeg")

    json_str = json.dumps(test2, indent=4)
    with open("../data/fridge.json", "w") as f:
        f.write(json_str)

    with open("../data/fridge.json", "r") as f:
        data2 = json.load(f)

    print(data2)
    print(type(data2))
