import json

import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Hm_1_2'  # name_gender_type
    allowed_domains = ['www2.hm.com']
    start_urls = [
        # 'https://www2.hm.com/en_ca/sale/shopbypr38oductladies/view-all/_jcr_content/main/productlisting_b48c.display.json?sort=stock&image-size=small&image=model&offset=0&page-size=13'
        'https://www2.hm.com/en_ca/sale/shopbyproductladies/view-all/_jcr_content/main/productlisting_b48c.display.json?sort=stock&image-size=small&image=stillLife&offset=36&page-size=259'

    ]
    base_url = 'https://www2.hm.com'
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
    }

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
        products = json_response.get('products')
        for product in products:
            item = ProductItem()
            image_url = product.get('image')[0].get('src')
            if 'https:' not in image_url:
                image_url = 'https:' + image_url
            hq_image_url = image_url.replace('/product/style', '/product/main')

            item['title'] = product.get('title')
            item['price'] = product.get('price')
            item['sale_price'] = product.get('redPrice')
            item['image_urls'] = [image_url, hq_image_url]
            item['product_link'] = self.base_url + product.get('link')
            yield item
