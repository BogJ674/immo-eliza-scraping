import scrapy

class PropertyItem(scrapy.Item):
    """Dynamic Scrapy Item that accepts any field."""
    def __setitem__(self, key, value):
        self.fields.setdefault(key, scrapy.Field())
        super().__setitem__(key, value)
