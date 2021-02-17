# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ProductItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    price = scrapy.Field()
    sale_price = scrapy.Field()
    product_link = scrapy.Field()
    status = scrapy.Field()
