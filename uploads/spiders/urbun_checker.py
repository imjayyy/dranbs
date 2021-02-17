from datetime import timedelta
from shutil import which

import scrapy
from django.utils import timezone
from scrapy_selenium import SeleniumRequest

from backend.models import Product
from scrapy_app.items import ProductItem


class BrokenLinksSpider(scrapy.Spider):
    name = 'urbun_checker'
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
            site__name__contains='Urban-outfitters',
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
        item['status'] = response.status
        no_result_tag1 = response.css('.c-pwa-tile-no-results')
        no_result_tag2 = response.css('.c-pwa-404')
        no_result_tag3 = response.css('.c-pwa-product-oos-rec-tray__lead-message')
        if no_result_tag1 or no_result_tag2 or no_result_tag3:
            item['status'] = 404
        yield item
