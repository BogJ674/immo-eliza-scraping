import scrapy

class PropertyItem(scrapy.Item):
	property_id = scrapy.Field()
	locality = scrapy.Field()
	price = scrapy.Field()
	property_type = scrapy.Field()
	subtype = scrapy.Field()
	rooms = scrapy.Field()
	living_area = scrapy.Field()
	url = scrapy.Field()
