import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Allsaints_2_1'
    allowed_domains = ['www.ca.allsaints.com']
    domain = 'https://www.ca.allsaints.com'
    start_urls = ['https://www.ca.allsaints.com/men/new/style,any/colour,any/size,any/']

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
        products = response.css('div.product-item')
        for idx, product in enumerate(products):
            item = ProductItem()
            item['title'] = product.css('span.product-item__name__text::text').get()
            item['price'] = product.css('span.product-item__price::text').get().strip()
            image_url = product.css('img::attr(src)').get()
            if 'https:' not in image_url:
                image_url = 'https:' + image_url
            b = image_url.split('https://images.allsaints.com/products/')
            c = b[1].split('/')
            hq_image_url = "https://images.allsaints.com/products/900"
            for i, x in enumerate(c):
                if i != 0:
                    hq_image_url = "{0}/{1}".format(hq_image_url, x)
            item['image_urls'] = [image_url, hq_image_url]
            product_link = product.css('a.mainImg::attr(href)').get()
            item['product_link'] = self.domain + product_link
            yield item
