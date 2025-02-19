import scrapy
import time
from urllib.parse import urljoin


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
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
    }

    def parse(self, response):
        products = response.css(".product.one-product-in-row")

        if not products:
            self.logger.warning("Товары не найдены! Проверьте селекторы.")

        for product in products:
            product_url = urljoin(response.url, product.css(".title::attr(href)").get())

            item = {
                "timestamp": int(time.time()),
                "RPC": product.attrib.get("id"),
                "url": product_url,
                "title": self.get_title(product),
                "marketing_tags": self.get_marketing_tags(product),
                "brand": self.get_brand(product),
                "section": [
                    section.strip() for section in response.url.split("/")[3:-1]
                ],
                "price_data": self.get_price_data(product),
                "stock": self.get_stock_info(product),
                "assets": self.get_assets(product),
                "metadata": self.get_metadata(response),
                "variants": self.get_variants(product),
            }

            yield response.follow(product_url, self.parse_product, meta={"item": item})

        next_page = response.css(".pagination-next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def get_title(self, product):
        title = product.css(".title::text").get()
        return title.strip() if title else ""

    def get_marketing_tags(self, product):
        tags = []
        sticker_text = product.css(".sticker::text").get()
        if sticker_text:
            tags.append(sticker_text.strip())
        return tags

    def get_brand(self, product):
        return product.css(".brand::text").get() or ""

    def get_price_data(self, product):
        price_original = product.css(".price-wrapper .price-block del::text").get()
        price_current = product.css(".price-wrapper .price-block span::text").get()

        if price_original:
            price_original = float(price_original.replace("₽", "").strip())
        if price_current:
            price_current = float(price_current.replace("₽", "").strip())
        else:
            price_current = price_original

        sale_tag = None
        if price_original and price_current and price_original > price_current:
            discount = round((1 - price_current / price_original) * 100)
            sale_tag = f"Скидка {discount}%"

        return {
            "current": price_current,
            "original": price_original,
            "sale_tag": sale_tag,
        }

    def get_stock_info(self, product):
        return {
            "in_stock": bool(product.css(".price-block")),
            "count": 0,
        }

    def get_assets(self, product):
        main_image = product.css(
            ".images-container link[itemprop=contentUrl]::attr(href)"
        ).get()
        set_images = product.css(".images-container img::attr(src)").getall()
        return {
            "main_image": main_image,
            "set_images": set_images,
            "view360": [],
            "video": [],
        }

    def get_metadata(self, response):
        description = response.css("meta[itemprop=description]::attr(content)").get()
        return {"__description": description} if description else {}

    def get_variants(self, product):
        variant_text = product.css(".variants-count::text").get()
        return (
            int(variant_text.split()[0])
            if variant_text and variant_text.split()[0].isdigit()
            else 0
        )

    def parse_product(self, response):
        item = response.meta["item"]
        metadata = item["metadata"]

        characteristics = response.css(".characteristics div::text").getall()
        for i in range(0, len(characteristics), 2):
            key = characteristics[i].strip()
            value = (
                characteristics[i + 1].strip() if i + 1 < len(characteristics) else ""
            )
            metadata[key] = value

        yield item
