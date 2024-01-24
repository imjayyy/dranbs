import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Fashionbunker_1_2'  # name_gender_type
    allowed_domains = ['us.fashionbunker.com']
    start_urls = ['https://fashionbunker.com/collections/sale?page=%s' % page for page in range(1, 31)]

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
        products = response.css('.product-grid > li.grid__item')

        for idx, product in enumerate(products):
            item = ProductItem()
            title = product.css('h3.card__heading a span::text').get()
            if title:
                item['title'] = title.strip()
            else:
                continue
            price = product.css('.price-item--sale::text').get()

            if price:
                item['price'] = price
            else:
                continue

            image_url = product.css('div.card__media img::attr(src)').get()
            if image_url:
                item['image_urls'] = ['https:' + image_url, 'https:' + image_url]
            else:
                continue

            product_link = product.css('a.card__media-link::attr(href)').get()
            item['product_link'] = self.base_url + product_link
            yield item
