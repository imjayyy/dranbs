import json

import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Joe-fresh_1_1'  # name_gender_type
    allowed_domains = ['www.joefresh.com']
    root_url = 'https://www.joefresh.com/ca'
    start_urls = [
        'https://www.joefresh.com/ca/**/c/10008/plpData?q=:relevance&sort=relevance&page=0&t=1602642282265',
        'https://www.joefresh.com/ca/**/c/10008/plpData?q=:relevance&sort=relevance&page=1&t=1602642282265',
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
        result = json_response[0]
        products = result['results']
        for product in products:
            item = ProductItem()
            item['title'] = product.get('name')
            item['price'] = product.get('minEffectivePrice').get('currencyIso') + product.get('minEffectivePrice').get('formattedValue')
            images = product.get('images')
            item['image_urls'] = [
                images.get('hover')[0],
                images.get('hover')[0]
            ]

            item['product_link'] = self.root_url + product.get('url')
            yield item
