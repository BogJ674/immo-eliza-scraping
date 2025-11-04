import re
import scrapy
from urllib.parse import urljoin
from scrapy_playwright.page import PageMethod
from scrapy.exporters import CsvItemExporter
from immoeliza.items import PropertyItem


# --- Custom dynamic CSV exporter ---
class DynamicCsvItemExporter(CsvItemExporter):
    """Automatically sets CSV headers from the first item."""
    def _write_headers_and_set_fields_to_export(self, item):
        if not self.fields_to_export:
            self.fields_to_export = list(item.keys())
        super()._write_headers_and_set_fields_to_export(item)


# --- Local abort_request (works for any scrapy-playwright version) ---
async def abort_request(request):
    # Keep CSS/JS for layout; drop heavy non-essentials
    if request.resource_type in ["image", "font", "media", "other"]:
        return True
    return False


class ImmovlanBrusselsSpider(scrapy.Spider):
    name = "immovlan_brussels"
    allowed_domains = ["immovlan.be", "www.immovlan.be"]
    base_search = "https://immovlan.be/en/real-estate/house/for-sale?municipals=brussels&page={page}"

    custom_settings = {
        # Speed & politeness
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.25,

        # Feed export (dynamic headers)
        "FEED_EXPORTERS": {
            "dynamic_csv": "immoeliza.spiders.immovlan_brussels.DynamicCsvItemExporter",
        },
        "FEEDS": {
            "data/immo_brussels.csv": {
                "format": "dynamic_csv",
                "encoding": "utf8",
                "overwrite": True,
            },
        },

        # Playwright
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 45000,
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
        "PLAYWRIGHT_ABORT_REQUEST": "immoeliza.spiders.immovlan_brussels.abort_request",

        # Headers
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

    # ---------------------------
    # Entry: listing pages (Scrapy only)
    # ---------------------------
    def start_requests(self):
        # Brussels has up to 8 pages
        for page in range(1, 9):
            url = self.base_search.format(page=page)
            yield scrapy.Request(url, callback=self.parse_listing)

    def parse_listing(self, response):
        """
        Parse a listing page and enqueue detail pages.
        We avoid heavy rendering here — Scrapy-only.
        """
        # Extract detail links by pattern (relative or absolute)
        # Accept both www and non-www forms
        hrefs = response.css("a::attr(href)").getall()
        detail_paths = [
            h for h in hrefs
            if re.search(r"/en/detail/", h or "")
        ]

        seen = set()
        for href in detail_paths:
            abs_url = urljoin(response.url, href)
            # Normalize to immovlan.be (without forcing www)
            if "immovlan.be/en/detail/" not in abs_url:
                continue
            if abs_url in seen:
                continue
            seen.add(abs_url)

            # First try static HTML; if not enough, we’ll fallback to Playwright inside parse_detail()
            yield scrapy.Request(
                abs_url,
                callback=self.parse_detail_static_first,
                dont_filter=True,
            )

        # Optional: robust pagination if pages > 8 someday
        # next_href = response.css("a[rel='next']::attr(href)").get()
        # if next_href:
        #     yield response.follow(next_href, callback=self.parse_listing)

    # ---------------------------
    # Detail page – Scrapy first, then Playwright fallback if needed
    # ---------------------------
    def parse_detail_static_first(self, response):
        """
        Try to extract directly (fast path). If Financial + More info are not present,
        retry via Playwright render.
        """
        has_financial = bool(response.css("div.financial"))
        has_general = bool(response.css("div.general-info"))

        if has_financial and has_general:
            yield from self._extract_item(response)
        else:
            # Fallback to rendered page (cookie, JS, lazy sections)
            yield scrapy.Request(
                response.url,
                callback=self.parse_detail_rendered,
                dont_filter=True,
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
                        PageMethod("wait_for_timeout", 1500),
                        PageMethod("wait_for_load_state", "networkidle"),
                    ],
                },
            )

    def parse_detail_rendered(self, response):
        """Rendered version: only accept items that have both sections."""
        has_financial = bool(response.css("div.financial"))
        has_general = bool(response.css("div.general-info"))

        if not (has_financial and has_general):
            self.logger.info(f"SKIP (no required sections): {response.url}")
            return

        yield from self._extract_item(response)

    # ---------------------------
    # Extraction
    # ---------------------------
    def _extract_item(self, response):
        """
        Extract all fields from Financial details + More information.
        Only called when both sections exist.
        """
        item = PropertyItem()
        item["url"] = response.url

        # IDs from URL
        parts = response.url.strip("/").split("/")
        item["postal_code"] = parts[-3] if len(parts) > 2 else ""
        item["municipality"] = parts[-2] if len(parts) > 1 else ""
        item["property_id"] = parts[-1].upper()

        # Financial details: <div class="financial"><ul><li><strong>Label</strong>: Value</li>...</ul></div>
        for li in response.css("div.financial li"):
            label = li.css("strong::text").get()
            value_full = li.xpath("normalize-space(string())").get()
            if not label:
                continue
            value = value_full.replace(label, "").replace(":", "").strip()
            item[self._norm(label)] = self._clean(value)

        # More information: <div class="general-info"> ... <div class="data-row-wrapper"><div><h4>Label</h4><p>Value</p></div> ...</div>
        for block in response.css("div.general-info div.data-row div.data-row-wrapper > div"):
            label = block.css("h4::text").get()
            value = block.css("p::text").get()
            if label and value:
                item[self._norm(label)] = self._clean(value)

        # Fallbacks (summary bits)
        price_text = response.css("div.detail-price::text").get()
        if price_text:
            item.setdefault("price", self._clean(price_text))

        title_text = response.css("div.detail-title h1::text").get()
        if title_text:
            item.setdefault("property_type", self._clean(title_text))

        self.logger.info(f"OK {response.url} → {len(item)} fields")
        yield item

    # ---------------------------
    # Utils
    # ---------------------------
    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip()) if text else ""

    def _norm(self, label: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", label.lower().strip()) if label else ""
