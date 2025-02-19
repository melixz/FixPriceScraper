BOT_NAME = "fix_price_scraper"

SPIDER_MODULES = ["fix_price_scraper.spiders"]
NEWSPIDER_MODULE = "fix_price_scraper.spiders"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

DOWNLOADER_MIDDLEWARES = {
    "scrapy_cloudflare_middleware.middlewares.CloudFlareMiddleware": 560,
    "fix_price_scraper.middlewares.ProxyMiddleware": 1,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
}

CONCURRENT_REQUESTS = 10
DOWNLOAD_DELAY = 2

USE_PROXY = False
PROXY_LIST = ["http://10.10.1.10:3128", "http://10.10.1.11:3128"]

FEEDS = {
    "data/products.json": {
        "format": "json",
        "encoding": "utf8",
        "store_empty": False,
        "fields": [
            "timestamp",
            "RPC",
            "url",
            "title",
            "marketing_tags",
            "brand",
            "section",
            "price_data",
            "stock",
            "assets",
            "metadata",
            "variants",
        ],
        "overwrite": True,
    },
}
