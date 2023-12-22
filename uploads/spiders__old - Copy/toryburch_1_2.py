import json

import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Tory-burch_1_2'  # name_gender_type
    allowed_domains = ['www.toryburch.com']
    base_url = 'https://www.toryburch.com'
    image_base_url = 'https://s7.toryburch.com/is/image/ToryBurch'
    start_urls = [
        'https://www.toryburch.com/api/prod-r2/v6/categories/clothing-sale/products?limit=50&site=ToryBurch_US',
        'https://www.toryburch.com/api/prod-r2/v6/categories/clothing-sale/products?limit=50&offset=50&site=ToryBurch_US',
        'https://www.toryburch.com/api/prod-r2/v6/categories/clothing-sale/products?limit=50&offset=100&site=ToryBurch_US',
        'https://www.toryburch.com/api/prod-r2/v6/categories/clothing-sale/products?limit=50&offset=150&site=ToryBurch_US',
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

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36 Edg/86.0.622.38',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,ko;q=0.8,fr;q=0.7',
            'X-API-Key': 'yP6bAmceig0QmrXzGfx3IG867h5jKkAs'
        }

        for url in self.start_urls:
            yield scrapy.http.Request(url, headers=headers, dont_filter=True)

    def parse(self, response, **kwargs):
        json_response = json.loads(response.body)
        products = json_response['products']
        for product in products:
            item = ProductItem()
            product_id = product.get('id')
            product_name = product.get('name')
            product_name = product_name.replace(' ', '-')
            product_name = product_name.lower()
            product_swatch = product.get('swatches')[0]
            color_number = product_swatch.get('colorNumber')
            product_link = "{0}/{1}/{2}.html?color={3}".format(self.base_url, product_name, product_id, color_number)

            item['title'] = product.get('title')
            item['price'] = "{0} {1}".format(product.get('price').get('currency'), product.get('price').get('max'))
            item['sale_price'] = "{0} {1}".format(product.get('price').get('currency'), product.get('price').get('min'))
            image_id = product_swatch.get('images')[0]
            item['image_urls'] = [
                "{0}/{1}-main.{2}.pdp-376x428.jpg".format(self.image_base_url, product_name, image_id),
                "{0}/{1}-main.{2}.pdp-720x819.jpg".format(self.image_base_url, product_name, image_id),
            ]

            item['product_link'] = product_link
            yield item
