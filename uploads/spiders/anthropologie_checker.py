from datetime import timedelta

import scrapy
from django.utils import timezone
from scrapy import signals
from scrapy_selenium import SeleniumRequest

from backend.models import Product
from scraping.models import ProductChecker
from scrapy_app.items import ProductItem


class BrokenLinksSpider(scrapy.Spider):
    name = 'anthropologie_checker'
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 30,
        'SELENIUM_DRIVER_NAME': 'firefox',
        'SELENIUM_COMMAND_EXECUTOR': 'http://localhost:4444/wd/hub',
        'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
        # 'SELENIUM_DRIVER_ARGUMENTS': [],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_selenium.SeleniumMiddleware': 800,
        },
        'ITEM_PIPELINES': {
            'scrapy_app.pipelines.ProductUpdatePipeline': 300,
        }
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(BrokenLinksSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider, reason):
        try:
            scraper = ProductChecker.objects.get(name=spider.name)
            scraper.last_scraped = timezone.now()
            scraper.save()
        except ProductChecker.DoesNotExist:
            pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = []
        time_threshold = timezone.now() - timedelta(days=30)
        products = Product.objects.filter(
            site__name__contains='Anthropologie',
            inserted_at__lt=time_threshold
        ).order_by('inserted_at')
        for product in products:
            self.start_urls.append(product.product_link)

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(url=url)

    def parse(self, response, **kwargs):
        item = ProductItem()
        item['product_link'] = response.request.url
        item['status'] = 200
        no_result_tag = response.css('.c-pwa-product-oos-rec-tray__lead-message')
        no_result_tag1 = response.css(".s-404-text")
        if no_result_tag or no_result_tag1:
            item['status'] = 404
        yield item
