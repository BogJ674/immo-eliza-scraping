# scraper/spiders/immoeliza_spider.py
# ✅ Fixed: Playwright argument structure and consistent indentation

import scrapy
from scrapy_playwright.page import PageMethod
from scraper.items import PropertyItem


class ImmoElizaSpider(scrapy.Spider):
	name = "immoeliza"
	allowed_domains = ["immovlan.be"]

	start_urls = [
		"https://www.immovlan.be/en/real-estate?transactiontypes=for-sale,in-public-sale&page=1"
	]

	custom_settings = {
		"PLAYWRIGHT_INCLUDE_PAGE": True,
		"PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
		"CONCURRENT_REQUESTS": 2,
		"DOWNLOAD_DELAY": 1.5,
		"FEEDS": {
			"data/raw/immoeliza_ghent.csv": {"format": "csv", "overwrite": True},
		},
		"DOWNLOAD_HANDLERS": {
			"http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
			"https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
		},
		"TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
		"DEFAULT_REQUEST_HEADERS": {
			"User-Agent": (
				"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/120.0.6099.110 Safari/537.36"
			),
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
			"Accept-Language": "en-US,en;q=0.9",
			"Referer": "https://www.google.com/",
			"Accept-Encoding": "gzip, deflate, br",
			"Connection": "keep-alive",
		},
		"PLAYWRIGHT_LAUNCH_OPTIONS": {
			"headless": True,
			"args": ["--disable-blink-features=AutomationControlled"],
		},
	}

	# ---------------------------
	def start_requests(self):
		for url in self.start_urls:
			yield scrapy.Request(
				url,
				meta={
					"playwright": True,
					"playwright_include_page": True,
					"playwright_page_methods": [
						PageMethod("set_viewport_size", {"width": 1366, "height": 768}),
						PageMethod(
							"add_init_script",
							"Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
						),
						PageMethod("wait_for_timeout", 1400),
					],
				},
				callback=self.parse_with_playwright,
			)

	# ---------------------------
	async def parse_with_playwright(self, response):
		page = response.meta.get("playwright_page")
		self.logger.info("✅ Listing page loaded — checking cookie popup & rendering...")

		try:
			await page.click("button[id*='didomi-notice-agree-button']", timeout=4000)
			self.logger.info("🍪 Cookie consent accepted")
			await page.wait_for_timeout(600)
		except Exception:
			self.logger.debug("No cookie popup or click failed (continuing)")

		try:
			await page.wait_for_selector(
				"article.list-view-item, div.list-view, a[href*='/detail/']",
				timeout=20000,
			)
		except Exception:
			html = await page.content()
			with open("debug_page.html", "w", encoding="utf-8") as f:
				f.write(html)
			self.logger.error("❌ Listing container not found — saved debug_page.html")
			await page.close()
			return

		# Extract property links
		links = await page.eval_on_selector_all(
			"article.list-view-item a[href*='/detail/'], "
			"a[href*='/detail/'].card, "
			"a.card__title-link[href*='/detail/']",
			"els => els.map(e => e.href)",
		)
		self.logger.info(f"🔗 Found {len(links)} property links")

		for url in links[:5]:
			yield scrapy.Request(
				url,
				meta={
					"playwright": True,
					"playwright_include_page": True,
					"playwright_page_methods": [
						PageMethod("set_viewport_size", {"width": 1366, "height": 768}),
						PageMethod(
							"add_init_script",
							"Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
						),
						PageMethod(
							"wait_for_selector",
							"main, div.property__main, div[class*='classified']",
							timeout=15000,
						),
					],
				},
				callback=self.parse_property,
			)

		await page.close()

	# ---------------------------
	async def parse_property(self, response):
		page = response.meta.get("playwright_page")
		item = PropertyItem()
		item["url"] = response.url
		item["property_id"] = response.url.rstrip("/").split("/")[-1]

		try:
			await page.wait_for_selector(
				"main, div.property__main, div[class*='classified']",
				timeout=15000,
			)
		except Exception:
			html = await page.content()
			with open("debug_property.html", "w", encoding="utf-8") as f:
				f.write(html)
			self.logger.error("❌ Property main content not found — saved debug_property.html")

		async def eval_sel(sel, transform):
			try:
				return await page.eval_on_selector(sel, transform)
			except Exception:
				return None

		locality = await eval_sel('meta[property="og:title"]', "el => el?.content?.trim()")
		if not locality:
			locality = await eval_sel("h1", "el => el?.innerText?.trim()")
		item["locality"] = (locality or "").strip()

		price = await eval_sel(
			"strong:has-text('€'), span:has-text('€'), "
			".property__price, .classified__price",
			"el => el?.innerText?.replace('€','').replace('\\u202f','').trim()",
		)
		item["price"] = price or ""

		title = await eval_sel("h1", "el => el?.innerText?.trim()") or ""
		item["property_type"] = (
			title.split("for sale")[0].strip()
			if "for sale" in title.lower()
			else title.split(" - ")[0].strip()
		)
		subtype = ""
		if "for sale" in title.lower():
			parts = title.split("for sale", 1)
			subtype = parts[1].strip() if len(parts) > 1 else ""
		item["subtype"] = subtype

		rooms = await eval_sel(
			"li:has-text('bedroom'), span:has-text('bedroom'), [itemprop='numberOfBedrooms']",
			"el => el?.innerText?.trim() || el?.content",
		)
		item["rooms"] = rooms or ""

		living_area = await eval_sel(
			"li:has-text('m²'), span:has-text('m²'), [itemprop='floorSize']",
			"el => el?.innerText?.trim() || el?.content",
		)
		item["living_area"] = living_area or ""

		# Save debug and close
		try:
			html = await page.content()
			with open(f"debug_property_{item['property_id']}.html", "w", encoding="utf-8") as f:
				f.write(html)
			await page.close()
		except Exception:
			pass

		yield item
