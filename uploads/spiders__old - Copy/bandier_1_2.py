import json

import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Bandier_1_2'  # name_gender_type
    allowed_domains = ['www.bandier.com']
    start_urls = [
        'https://api.searchspring.net/api/search/search.json?siteId=96jhb3&bgfilter.collection_id=163826925602&&resultsFormat=native&page=%s' % page for page in range(1, 4)
    ]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ProductSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider, reason):
        a = spider.name.split('_')
        try:
            scraper = Scraper.objects.get(site__name=a[0], site__gender=int(a[1]), site__type=int(a[2]))
            scraper.last_scraped = timezone.now()
            scraper.save()
        except Scraper.DoesNotExist:
            pass

    def parse(self, response, **kwargs):
        json_response = json.loads(response.body)
        products = json_response.get('results')
        for product in products:
            item = ProductItem()
            image_url = product.get('imageUrl')

            item['title'] = product.get('title')
            item['price'] = "${0}".format(product.get('msrp'))
            item['sale_price'] = "${0}".format(product.get('price'))
            item['image_urls'] = [image_url, image_url]
            item['product_link'] = product.get('url')
            yield item
