from datetime import timedelta
from shutil import which

import scrapy
from django.utils import timezone
from scrapy_selenium import SeleniumRequest

from backend.models import Product
from scrapy_app.items import ProductItem


class BrokenLinksSpider(scrapy.Spider):
    name = 'simons_checker'
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 10,
        'SELENIUM_DRIVER_NAME': 'firefox',
        'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
        'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
        # 'SELENIUM_DRIVER_ARGUMENTS': [],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_selenium.SeleniumMiddleware': 800,
        },
        'ITEM_PIPELINES': {
            'scrapy_app.pipelines.ProductUpdatePipeline': 300,
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = []
        time_threshold = timezone.now() - timedelta(days=30)
        products = Product.objects.filter(
            site__name__contains='Simons',
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
        out_of_stock_banner = response.css('#outOfStockBanner')
        out_of_stock_popup = response.css('#OutOfStockPopup')
        item['status'] = 200
        if out_of_stock_banner or out_of_stock_popup:
            item['status'] = 404
        yield item
