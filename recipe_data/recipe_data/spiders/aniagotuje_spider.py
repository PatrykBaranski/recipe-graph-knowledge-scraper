import json

from scrapy import Spider, Request

class AniaGotujeSpider(Spider):
    name = "aniagotuje_spider"
    allowed_domains = ["aniagotuje.pl"]
    start_urls = ["https://api.aniagotuje.pl/client/posts/search?perPage=200&page=0&sort=publish,desc"]
    custom_settings = {
        "AUTOTHROTTLE_ENABLED": True,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "DOWNLOAD_DELAY": 0.2,
        "ITEM_PIPELINES": {
            'recipe_data.pipelines.RecipeDataPipeline': 300,
        },
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)


    def parse(self, response):
        curr_page = response.meta.get('curr_page', 0)
        data = json.loads(response.text)


        for recipie_info in data.get('content'):
            recipie_slug = recipie_info.get('slug')
            recipe_url = f'https://api.aniagotuje.pl/client/post/{recipie_slug}'
            yield Request(
                recipe_url,
                callback=self.parse_recipe,
            )

        max_page = data.get('totalPages')
        if curr_page < max_page - 1:
            next_page = curr_page + 1
            next_page_url = self.get_next_page_url(next_page)

            yield Request(next_page_url, callback=self.parse, meta={'curr_page': next_page})


    def parse_recipe(self, response):
        data = json.loads(response.text)
        yield data

    def get_next_page_url(self, curr_page):
       return  f'https://api.aniagotuje.pl/client/posts/search?perPage=24&page={curr_page}&sort=publish,desc'