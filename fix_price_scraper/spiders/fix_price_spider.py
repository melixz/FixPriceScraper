import scrapy
import json
from scrapy.http import Response
from datetime import datetime, timezone
from fix_price_scraper.items import FixPriceScraperItem


class FixPriceSpider(scrapy.Spider):
    name = "fix_price"

    start_urls = [
        "https://api.fix-price.com/buyer/v1/product/in/kosmetika-i-gigiena/ukhod-za-polostyu-rta?page=1&limit=24&sort=sold",
        "https://api.fix-price.com/buyer/v1/product/in/kosmetika-i-gigiena/ukhod-za-telom?page=1&limit=24&sort=sold",
        "https://api.fix-price.com/buyer/v1/product/in/produkty-i-napitki/morozhenoe?page=1&limit=24&sort=sold",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://fix-price.com/",
        "Origin": "https://fix-price.com",
        "Content-Type": "application/json",
        "x-language": "ru",
        "x-city": "55",
        "x-key": "d2f5ec19a69f330baa6a90bdb6ee98a2",
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                method="POST",
                headers=self.headers,
                body=json.dumps({}),
                callback=self.parse,
            )

    def parse(self, response: Response, **kwargs):
        if response.status != 200:
            self.logger.error(f"Ошибка {response.status}: {response.text}")
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error("Ошибка парсинга JSON!")
            return

        if isinstance(data, list):
            products = data
        elif isinstance(data, dict) and "products" in data:
            products = data["products"]
        else:
            self.logger.warning(f"Неизвестный формат JSON: {data}")
            return

        for item in products:
            product = FixPriceScraperItem()
            product["timestamp"] = datetime.now(timezone.utc).isoformat()
            product["RPC"] = item.get("sku", item.get("id"))
            product["url"] = f"https://fix-price.com/catalog/{item.get('url')}"
            product["title"] = item.get("title")
            product["marketing_tags"] = []
            product["brand"] = (
                item["brand"]["title"] if item.get("brand") else "No Brand"
            )
            product["section"] = (
                item["category"]["title"] if item.get("category") else "No Category"
            )
            product["price_data"] = {
                "current": float(item["price"]) if item.get("price") else None,
                "original": float(item["specialPrice"]["price"])
                if item.get("specialPrice")
                else None,
                "currency": "RUB",
            }
            product["stock"] = {"count": item.get("inStock")}
            product["assets"] = {
                "main_image": item["images"][0]["src"]
                if item.get("images") and len(item["images"]) > 0
                else "",
                "additional_images": [img["src"] for img in item.get("images", [])[1:]],
            }
            product["metadata"] = {}
            product["variants"] = []

            yield product

        current_page = int(response.url.split("page=")[1].split("&")[0])
        next_page = response.url.replace(
            f"page={current_page}", f"page={current_page + 1}"
        )

        if products and next_page:
            yield scrapy.Request(
                url=next_page,
                method="POST",
                headers=self.headers,
                body=json.dumps({}),
                callback=self.parse,
            )
