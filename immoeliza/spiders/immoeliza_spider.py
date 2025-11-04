import scrapy
import re
from scrapy_playwright.page import PageMethod
from immoeliza.items import PropertyItem


class ImmoElizaSpider(scrapy.Spider):
    name = "immoeliza"
    allowed_domains = ["immovlan.be"]
    start_urls = [
        "https://www.immovlan.be/en/detail/villa/for-sale/7180/seneffe/vwd15538"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 120000,
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "FEEDS": {
            "data/immoeliza_full.csv": {
                "format": "csv",
                "encoding": "utf8",
                "overwrite": True,
            },
        },
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.6261.70 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": False,  # Change to True when confirmed working
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1400,900",
            ],
        },
    }

    async def start(self):
        """Main Playwright flow: accept cookies, scroll, and wait for full data."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),

                        # --- Accept cookie banner ---
                        PageMethod(
                            "evaluate",
                            """() => {
                                const btn = document.querySelector('#didomi-notice-agree-button,[aria-label*="Accept"]');
                                if (btn) btn.click();
                            }""",
                        ),
                        PageMethod("wait_for_timeout", 2000),

                        # --- Scroll down progressively to trigger all lazy sections ---
                        PageMethod(
                            "evaluate",
                            """async () => {
                                for (let i = 0; i < 15; i++) {
                                    window.scrollBy(0, window.innerHeight);
                                    await new Promise(r => setTimeout(r, 800));
                                }
                            }"""
                        ),
                        PageMethod("wait_for_timeout", 5000),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                },
                callback=self.parse_property,
            )

    async def parse_property(self, response):
        item = PropertyItem()
        item["url"] = response.url

        # --- Basic identifiers ---
        parts = response.url.strip("/").split("/")
        item["postal_code"] = parts[-3] if len(parts) > 2 else ""
        item["municipality"] = parts[-2] if len(parts) > 1 else ""
        item["property_id"] = parts[-1].upper()

        # --- 1️⃣ Financial details ---
        for li in response.css("div.financial li"):
            label = li.css("strong::text").get()
            value = li.xpath("normalize-space(string())").get()
            if label:
                value = value.replace(label, "").replace(":", "").strip()
                item[self.normalize(label)] = self.clean(value)

        # --- 2️⃣ More information (general-info) ---
        for block in response.css("div.general-info div.data-row div.data-row-wrapper > div"):
            label = block.css("h4::text").get()
            value = block.css("p::text").get()
            if label and value:
                item[self.normalize(label)] = self.clean(value)

        # --- 3️⃣ Fallback: Price and Property type ---
        item.setdefault("price", response.css("div.detail-price::text").get(default="").strip())
        item.setdefault("property_type", response.css("div.detail-title h1::text").get(default="").strip())

        # --- 4️⃣ Debug dump for verification ---
        with open("page_dump.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        self.logger.info(f"✅ Extracted {len(item.keys())} fields from {response.url}")
        yield item

    # ---- Helpers ----
    def clean(self, text):
        """Normalize whitespace and remove stray characters."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    def normalize(self, label):
        """Convert labels to safe snake_case keys."""
        if not label:
            return ""
        label = label.lower().strip()
        label = re.sub(r"[^a-z0-9]+", "_", label)
        return label.strip("_")
