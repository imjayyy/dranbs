from shutil import which

import scrapy
from django.utils import timezone
from scrapy import signals
from scrapy_selenium import SeleniumRequest

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Old-navy_1_1'  # name_gender_type
    allowed_domains = ['oldnavy.gapcanada.ca']
    start_urls = [
        'https://oldnavy.gapcanada.ca/browse/category.do?cid=10018',
        'https://oldnavy.gapcanada.ca/browse/category.do?cid=10018#pageId=1'
    ]
    custom_settings = {
        'SELENIUM_DRIVER_NAME': 'firefox',
        # 'SELENIUM_DRIVER_NAME': 'chrome',
        'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
        # 'SELENIUM_DRIVER_EXECUTABLE_PATH': which('chromedriver'),
        'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
        # 'SELENIUM_DRIVER_ARGUMENTS': [],
        # 'SELENIUM_PROXY': '46.250.220.148:3128',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_app.middlewares.SeleniumMiddleware': 800,
        },
        'ITEM_PIPELINES': {
            'scrapy_app.pipelines.ProductPipeline': 300,
            'scrapy_app.pipelines.ImagesWithSeleniumProxyPipeline': 2,
        }
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

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url)

    def parse(self, response, **kwargs):
        products = response.css('.product-card')
        for product in products:
            title = product.css('.product-card__name::text').get()
            highlight_price = product.css('.product-price__highlight::text').get()
            price = product.css('.product-card-price > div:first-child > span > span::text').get()
            image_url = product.css('img::attr(src)').get()
            product_link = product.css('.product-card__link::attr(href)').get()

            print("title: {0}".format(title))
            print("price: {0}".format(price))
            print("highlight: {0}".format(highlight_price))
            print("image_url: {0}".format(image_url))
            print("product_link: {0}".format(product_link))

            if title and (highlight_price or price) and image_url and product_link:
                item = ProductItem()
                item['title'] = title
                if price:
                    item['price'] = price
                else:
                    item['price'] = highlight_price
                item['image_urls'] = [image_url, image_url]
                item['product_link'] = product_link
                yield item
