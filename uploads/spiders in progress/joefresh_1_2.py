import json

import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem
from . import get_scraperapi_url


class ProductSpider(scrapy.Spider):
    name = 'Joe-fresh_1_2'  # name_gender_type
    allowed_domains = ['www.joefresh.com']
    root_url = 'https://www.joefresh.com/ca'
    start_urls = [
        'https://www.joefresh.com/ca/**/c/10057/plpData?q=:relevance&sort=popular-desc&page=%s&t=1602661758290' % page for page in range(0, 6)
    ]
    for i in range(start_urls):
        start_urls[i] = get_scraperapi_url(start_urls[i])

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
            item['sale_price'] = product.get('minEffectivePrice').get('currencyIso') + product.get('minEffectivePrice').get('formattedValue')
            if product.get('minRegularPrice'):
                item['price'] = product.get('minRegularPrice').get('currencyIso') + product.get('minRegularPrice').get('formattedValue')
            images = product.get('images')
            item['image_urls'] = [
                images.get('hover')[0],
                images.get('hover')[0]
            ]

            item['product_link'] = self.root_url + product.get('url')
            yield item
