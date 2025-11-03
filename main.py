from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scraper.spiders.immoeliza_spider import ImmoElizaSpider

if __name__ == "__main__":
    process = CrawlerProcess(get_project_settings())
    process.crawl(ImmoElizaSpider)
    process.start()