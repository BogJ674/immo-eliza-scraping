import scrapy
import random
from scrapy_playwright.page import PageMethod
from immoeliza.items import PropertyItem


class ImmoElizaSpider(scrapy.Spider):
    name = "immoeliza"
    allowed_domains = ["immovlan.be"]
    start_urls = [
        "https://www.immovlan.be/en/projectdetail/24431-p-vk0101-tfjkrblr"
    ]

    # ---- User-Agent pool to randomize fingerprints ----
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]

    # ---- Spider settings ----
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
        "RETRY_ENABLED": True,
        "RETRY_HTTP_CODES": [403, 429, 503],
        "RETRY_TIMES": 3,

        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,

        "PLAYWRIGHT_CONTEXTS": {
            "default": {
                "viewport": {"width": 1366, "height": 768},
                "java_script_enabled": True,
                "ignore_https_errors": True,
                "bypass_csp": True,
            }
        },

        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },

        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",

        # ---- Output ----
        "FEEDS": {
            "data/immoeliza_single.csv": {"format": "csv", "encoding": "utf8", "overwrite": True},
        },
        "LOG_LEVEL": "INFO",
    }

    # ---- Start request with random UA + stealth Playwright ----
    def start_requests(self):
        headers = {"User-Agent": random.choice(self.USER_AGENTS)}
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                headers=headers,
                meta={
                    "playwright": True,
                    "playwright_context": "default",
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_timeout", random.randint(1500, 3000)),
                    ],
                },
                callback=self.parse_project,
                errback=self.errback,
            )

    # ---- Data extraction ----
    def parse_project(self, response):
        item = PropertyItem()
        item["url"] = response.url
        item["property_id"] = response.url.split("/")[-1].split("-")[0]
        item["locality"] = response.xpath("//h1/text()").get(default="").strip()
        item["price"] = response.xpath("//*[contains(text(),'€')]/text()").get(default="").strip()
        item["property_type"] = response.xpath("//*[contains(text(),'Type')]/following::text()[1]").get(default="").strip()
        item["subtype"] = response.xpath("//*[contains(text(),'Subtype')]/following::text()[1]").get(default="").strip()
        item["rooms"] = response.xpath("//*[contains(text(),'Bedroom')]/text()").get(default="").strip()
        item["living_area"] = response.xpath("//*[contains(text(),'m²')]/text()").get(default="").strip()
        yield item

    async def errback(self, failure):
        self.logger.error(f"[ERROR] {repr(failure)}")
