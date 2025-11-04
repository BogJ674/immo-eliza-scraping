import scrapy
import re
from scrapy_playwright.page import PageMethod
from immoeliza.items import PropertyItem
from scrapy.exporters import CsvItemExporter


# --- Custom dynamic CSV exporter ---
class DynamicCsvItemExporter(CsvItemExporter):
    """Automatically sets CSV headers based on first item."""
    def _write_headers_and_set_fields_to_export(self, item):
        if not self.fields_to_export:
            self.fields_to_export = list(item.keys())
        super()._write_headers_and_set_fields_to_export(item)


# --- Local abort_request for all scrapy-playwright versions ---
async def abort_request(request):
    """Cancel loading of heavy resources to improve speed."""
    if request.resource_type in ["image", "font", "media", "other"]:
        return True
    return False


class ImmoElizaHybridSpider(scrapy.Spider):
    name = "immoeliza_hybrid"
    allowed_domains = ["immovlan.be"]
    start_urls = [
        "https://www.immovlan.be/en/detail/villa/for-sale/7180/seneffe/vwd15538"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 4,
        "DOWNLOAD_DELAY": 0.5,

        # --- Feed export setup (Dynamic CSV) ---
        "FEED_EXPORTERS": {
            "dynamic_csv": "immoeliza.spiders.immoeliza_spider.DynamicCsvItemExporter",
        },
        "FEEDS": {
            "data/immoeliza_full.csv": {
                "format": "dynamic_csv",
                "encoding": "utf8",
                "overwrite": True,
            },
        },

        # --- Playwright configuration ---
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 60000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": [
                "--disable-gpu",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--window-size=1280,800",
            ],
        },

        # --- Use local abort function ---
        "PLAYWRIGHT_ABORT_REQUEST": "immoeliza.spiders.immoeliza_spider.abort_request",

        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # --- ENTRY POINT ---
    def start_requests(self):
        """Always render with Playwright to avoid 403 blocking and handle cookies."""
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod(
                            "evaluate",
                            """() => {
                                const btn = document.querySelector('#didomi-notice-agree-button,[aria-label*="Accept"]');
                                if (btn) btn.click();
                            }""",
                        ),
                        PageMethod(
                            "evaluate",
                            """() => {
                                let totalHeight = 0;
                                const distance = 400;
                                const timer = setInterval(() => {
                                    window.scrollBy(0, distance);
                                    totalHeight += distance;
                                    if (totalHeight >= document.body.scrollHeight) clearInterval(timer);
                                }, 300);
                            }""",
                        ),
                        PageMethod("wait_for_timeout", 6000),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                },
                callback=self.parse_property,
            )

    # --- PARSER ---
    def parse_property(self, response):
        """Extract data from a fully rendered property detail page."""
        item = PropertyItem()
        item["url"] = response.url

        # --- Basic IDs ---
        parts = response.url.strip("/").split("/")
        item["postal_code"] = parts[-3] if len(parts) > 2 else ""
        item["municipality"] = parts[-2] if len(parts) > 1 else ""
        item["property_id"] = parts[-1].upper()

        # --- Financial details ---
        for li in response.css("div.financial li"):
            label = li.css("strong::text").get()
            value = li.xpath("normalize-space(string())").get()
            if label:
                value = value.replace(label, "").replace(":", "").strip()
                item[self.normalize(label)] = self.clean(value)

        # --- More information (General info + sections) ---
        for block in response.css("div.general-info div.data-row div.data-row-wrapper > div"):
            label = block.css("h4::text").get()
            value = block.css("p::text").get()
            if label and value:
                item[self.normalize(label)] = self.clean(value)

        # --- Fallback key fields (price, type) ---
        price_text = response.css("div.detail-price::text").get()
        if price_text:
            item["price"] = self.clean(price_text)
        title_text = response.css("div.detail-title h1::text").get()
        if title_text:
            item["property_type"] = self.clean(title_text)

        # --- Debug snapshot for inspection ---
        with open("page_dump.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        self.logger.info(f"Extracted {len(item.keys())} fields from {response.url}")
        yield item

    # --- UTILITIES ---
    def clean(self, text):
        """Normalize whitespace and remove unwanted chars."""
        return re.sub(r"\s+", " ", text.strip()) if text else ""

    def normalize(self, label):
        """Convert label text into clean snake_case keys."""
        return re.sub(r"[^a-z0-9]+", "_", label.lower().strip()) if label else ""
