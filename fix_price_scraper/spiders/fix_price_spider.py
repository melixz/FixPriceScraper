import scrapy
import time


class FixPriceSpider(scrapy.Spider):
    name = "fix_price"
    allowed_domains = ["fix-price.com"]
    start_urls = [
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-polostyu-rta",
        "https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-telom",
        "https://fix-price.com/catalog/produkty-i-napitki/morozhenoe",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 10,
        "FEED_FORMAT": "json",
        "FEED_URI": "data/products.json",
    }

    def parse(self, response):
        product_links = response.css("a.product-card::attr(href)").getall()
        for link in product_links:
            yield response.follow(link, self.parse_product)

        next_page = response.css("a.pagination-next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_product(self, response):
        timestamp = int(time.time())

        title = response.css("h1.product-title::text").get()
        if title:
            title = title.strip()

        price = response.css("span.price__current::text").get()
        if price:
            price = float(price.replace("₽", "").strip())
        else:
            price = None

        original_price = response.css("span.price__original::text").get()
        if original_price:
            original_price = float(original_price.replace("₽", "").strip())
        else:
            original_price = price

        stock = response.css("span.stock-status span::text").get()
        in_stock = stock and "в наличии" in stock

        rpc = response.url.split("-")[-1].split(".")[0]

        images = response.css("div.product-gallery img::attr(src)").getall()

        description = response.css('meta[name="description"]::attr(content)').get()

        product_data = {
            "timestamp": timestamp,
            "RPC": rpc,
            "url": response.url,
            "title": title,
            "marketing_tags": [],
            "brand": "",
            "section": response.url.split("/")[3:-1],
            "price_data": {
                "current": price,
                "original": original_price,
                "sale_tag": None,
            },
            "stock": {
                "in_stock": in_stock,
                "count": 0,
            },
            "assets": {
                "main_image": images[0] if images else None,
                "set_images": images,
                "view360": [],
                "video": [],
            },
            "metadata": {
                "__description": description,
            },
            "variants": 0,
        }

        yield product_data
