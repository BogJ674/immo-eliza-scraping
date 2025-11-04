import re
import json
import time
from urllib.parse import urljoin

import scrapy
from scrapy.exporters import CsvItemExporter
from scrapy_playwright.page import PageMethod

from immoeliza.items import PropertyItem

# ---------- optional tqdm ------------
try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


# -------- Dynamic CSV exporter ----------
class DynamicCsvItemExporter(CsvItemExporter):
    def _write_headers_and_set_fields_to_export(self, item):
        if not self.fields_to_export:
            self.fields_to_export = list(item.keys())
        super()._write_headers_and_set_fields_to_export(item)


# -------- Abort heavy requests ----------
async def abort_request(request):
    if request.resource_type in ["image", "font", "media", "other"]:
        return True
    return False


# =====================================================
#   Tier 1 optimized spider - Full (992 pages)
# =====================================================
class ImmovlanHousesT1FullSpider(scrapy.Spider):
    """
    Crawl all Immovlan houses-for-sale pages (1–992).

    Usage:
      scrapy crawl immovlan_houses_t1_full -s LOG_FILE=log_full.txt
    """
    name = "immovlan_houses_t1_full"
    allowed_domains = ["immovlan.be", "www.immovlan.be"]

    base_search = "https://immovlan.be/en/real-estate/house/for-sale?page={page}"

    # ------------ init ------------
    def __init__(self, start_page: int = 1, max_pages: int = 992, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.max_pages = int(max_pages)

        self.t0 = None
        self.metrics = {
            "start_page": self.start_page,
            "max_pages": self.max_pages,
            "listing_pages_requested": 0,
            "detail_links_found": 0,
            "detail_requests_sent": 0,
            "items_exported": 0,
        }
        self._seen_details = set()

    # ------------ optimized settings ------------
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 20,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 16,
        "DOWNLOAD_DELAY": 0.05,

        "FEED_EXPORTERS": {
            "dynamic_csv": "immoeliza.spiders.immovlan_houses_t1_full.DynamicCsvItemExporter",
        },
        "FEEDS": {
            "data/immo_houses_t1_full.csv": {  # New file for full crawl
                "format": "dynamic_csv",
                "encoding": "utf8",
                "overwrite": True,
            },
        },

        # Playwright
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 20000,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": [
                "--disable-gpu",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1280,800",
            ],
        },
        "PLAYWRIGHT_ABORT_REQUEST": "immoeliza.spiders.immovlan_houses_t1_full.abort_request",

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

    # ------------ lifecycle ------------
    def open_spider(self, spider):
        self.t0 = time.monotonic()

    def close_spider(self, spider):
        elapsed = time.monotonic() - self.t0 if self.t0 else None
        self.metrics["elapsed_seconds"] = round(elapsed or 0.0, 2)
        metrics_path = f"data/metrics_immo_houses_t1_full.json"  # new metrics file
        try:
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Metrics written → {metrics_path}: {self.metrics}")
        except Exception as e:
            self.logger.warning(f"Failed to write metrics: {e}")

    # ------------ listing pages ------------
    def start_requests(self):
        end_page = self.start_page + self.max_pages - 1
        page_range = range(self.start_page, end_page + 1)
        iterator = tqdm(page_range, desc="Listing pages (1–992)") if tqdm else page_range

        for page in iterator:
            url = self.base_search.format(page=page)
            self.metrics["listing_pages_requested"] += 1
            yield scrapy.Request(url, callback=self.parse_listing)

    def parse_listing(self, response):
        hrefs = response.css("a::attr(href)").getall()
        detail_paths = [h for h in hrefs if re.search(r"/en/detail/", h or "")]
        iterator = tqdm(detail_paths, desc=f"Details page={response.url.split('=')[-1]}") if tqdm else detail_paths

        for href in iterator:
            abs_url = urljoin(response.url, href)
            if "immovlan.be/en/detail/" not in abs_url or abs_url in self._seen_details:
                continue
            self._seen_details.add(abs_url)
            self.metrics["detail_links_found"] += 1
            self.metrics["detail_requests_sent"] += 1
            yield scrapy.Request(abs_url, callback=self.parse_detail_static_first, dont_filter=True)

    # ------------ detail pages (static first) ------------
    def parse_detail_static_first(self, response):
        has_financial = bool(response.css("div.financial"))
        has_general = bool(response.css("div.general-info"))

        if has_financial and has_general:
            yield from self._extract_item(response)
        else:
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
                        PageMethod("wait_for_timeout", 500),
                    ],
                },
            )

    def parse_detail_rendered(self, response):
        has_financial = bool(response.css("div.financial"))
        has_general = bool(response.css("div.general-info"))

        if not (has_financial and has_general):
            return
        yield from self._extract_item(response)

    # ------------ extraction ------------
    def _extract_item(self, response):
        item = PropertyItem()
        item["url"] = response.url

        parts = response.url.strip("/").split("/")
        item["postal_code"] = parts[-3] if len(parts) > 2 else ""
        item["municipality"] = parts[-2] if len(parts) > 1 else ""
        item["property_id"] = parts[-1].upper()

        for li in response.css("div.financial li"):
            label = li.css("strong::text").get()
            value_full = li.xpath("normalize-space(string())").get()
            if not label:
                continue
            value = value_full.replace(label, "").replace(":", "").strip()
            item[self._norm(label)] = self._clean(value)

        for block in response.css("div.general-info div.data-row div.data-row-wrapper > div"):
            label = block.css("h4::text").get()
            value = block.css("p::text").get()
            if label and value:
                item[self._norm(label)] = self._clean(value)

        price_text = response.css("div.detail-price::text").get()
        if price_text:
            item.setdefault("price", self._clean(price_text))

        title_text = response.css("div.detail-title h1::text").get()
        if title_text:
            item.setdefault("property_type", self._clean(title_text))

        self.metrics["items_exported"] += 1
        if self.metrics["items_exported"] % 500 == 0:
            self.logger.info(f"Exported {self.metrics['items_exported']} items so far...")
        yield item

    # ------------ utils ------------
    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip()) if text else ""

    def _norm(self, label: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", label.lower().strip()) if label else ""
