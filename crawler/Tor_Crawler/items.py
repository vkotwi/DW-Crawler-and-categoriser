# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

# Defines "items" crawler will collect from a webpage


class TorCrawlerItem(Item):
    url = Field()
    response = Field()
    redirects = Field()
    status = Field()
