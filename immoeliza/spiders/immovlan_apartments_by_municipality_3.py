import re
import json
import time
from urllib.parse import urljoin

import scrapy
from scrapy.exporters import CsvItemExporter
from scrapy_playwright.page import PageMethod
from immoeliza.items import PropertyItem

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


class DynamicCsvItemExporter(CsvItemExporter):
    def _write_headers_and_set_fields_to_export(self, item):
        if not self.fields_to_export:
            self.fields_to_export = list(item.keys())
        super()._write_headers_and_set_fields_to_export(item)


async def abort_request(request):
    if request.resource_type in ["image", "font", "media", "other"]:
        return True
    return False


# =====================================================
#   Crawl Immovlan apartments by municipality (Top 50)
# =====================================================
class ImmovlanApartmentsByMunicipalitySpider(scrapy.Spider):
    """
    Crawl Immovlan apartments-for-sale for the top 50 Belgian municipalities.
    Each municipality covers itself and its suburbs.

    Usage:
      scrapy crawl immovlan_apartments_by_municipality -s LOG_FILE=log_apartments.txt
    """
    name = "immovlan_apartments_by_municipality_3"
    allowed_domains = ["immovlan.be", "www.immovlan.be"]

    base_search = (
        "https://immovlan.be/en/real-estate/apartment/for-sale?municipals={municipal}&page={page}"
    )

    municipalities = [
        
        "tournai", "uccle", "wavre", "turnhout", "herstal", "jette", "waterloo", "grimbergen", "heist-op-den-berg",
        "knokke-heist", "tienen", "beringen", "lommel", "halle", "ninove", "evergem", "dendermonde", "lier",
        "deinze", "geel", "edegem", "sint-pieters-leeuw", "oudenaarde"
    ]

    def __init__(self, max_pages: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_pages = int(max_pages)
        self.t0 = None
        self.metrics = {
            "municipalities_total": len(self.municipalities),
            "listing_pages_requested": 0,
            "detail_links_found": 0,
            "detail_requests_sent": 0,
            "items_exported": 0,
        }
        self._seen_details = set()

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 60,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 30,
        "DOWNLOAD_DELAY": 0.02,
        "FEED_EXPORTERS": {
            "dynamic_csv": "immoeliza.spiders.immovlan_apartments_by_municipality.DynamicCsvItemExporter",
        },
        "FEEDS": {
            "data/immo_apartments_by_municipality_3.csv": {
                "format": "dynamic_csv",
                "encoding": "utf8",
                "overwrite": True,
            },
        },
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
        "PLAYWRIGHT_ABORT_REQUEST": "immoeliza.spiders.immovlan_apartments_by_municipality.abort_request",
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

    def open_spider(self, spider):
        self.t0 = time.monotonic()

    def close_spider(self, spider):
        elapsed = time.monotonic() - self.t0 if self.t0 else None
        self.metrics["elapsed_seconds"] = round(elapsed or 0.0, 2)
        metrics_path = "data/metrics_immo_apartments_by_municipality.json"
        try:
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Metrics written → {metrics_path}: {self.metrics}")
        except Exception as e:
            self.logger.warning(f"Failed to write metrics: {e}")

    def start_requests(self):
        iterator = tqdm(self.municipalities, desc="Municipalities (apartments)") if tqdm else self.municipalities
        for municipal in iterator:
            for page in range(1, self.max_pages + 1):
                url = self.base_search.format(municipal=municipal, page=page)
                self.metrics["listing_pages_requested"] += 1
                yield scrapy.Request(url, callback=self.parse_listing, meta={"municipal": municipal, "page": page})

    def parse_listing(self, response):
        municipal = response.meta.get("municipal")
        hrefs = response.css("a::attr(href)").getall()
        detail_paths = [h for h in hrefs if re.search(r"/en/detail/", h or "")]
        iterator = tqdm(detail_paths, desc=f"{municipal} page={response.meta.get('page')}") if tqdm else detail_paths

        for href in iterator:
            abs_url = urljoin(response.url, href)
            if "immovlan.be/en/detail/" not in abs_url or abs_url in self._seen_details:
                continue
            self._seen_details.add(abs_url)
            self.metrics["detail_links_found"] += 1
            self.metrics["detail_requests_sent"] += 1
            yield scrapy.Request(abs_url, callback=self.parse_detail_static_first, dont_filter=True)

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

    def _extract_item(self, response):
        item = PropertyItem()
        item["url"] = response.url
        parts = response.url.strip("/").split("/")
        item["municipality_url"] = parts[-2] if len(parts) > 1 else ""
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
            self.logger.info(f"Exported {self.metrics['items_exported']} apartment items so far...")
        yield item

    def _clean(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.strip()) if text else ""

    def _norm(self, label: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", label.lower().strip()) if label else ""
