import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Scotch-soda_1_1'  # name_gender_type
    allowed_domains = ['www.scotch-soda.com']
    start_urls = [
        'https://www.scotch-soda.com/ca/en/women/new-arrivals?sz=120',
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
        products = response.css('div.product-tile')
        for idx, product in enumerate(products):
            item = ProductItem()
            item['title'] = product.css('.product__name::text').get().strip()
            item['price'] = product.css('.product__price::text').get().strip()
            image_url = product.css('img::attr(data-src)').get()
            item['image_urls'] = [image_url, image_url]
            item['product_link'] = product.css('a::attr(href)').get()
            yield item

