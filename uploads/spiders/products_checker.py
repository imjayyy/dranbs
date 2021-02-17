from datetime import timedelta
from shutil import which

import scrapy
from django.utils import timezone
from scrapy_selenium import SeleniumRequest

from backend.models import Product
from scrapy_app.items import ProductItem


class BrokenLinksSpider(scrapy.Spider):
    name = 'products_checker'
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

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.start_urls = []
        time_threshold = timezone.now() - timedelta(days=30)
        products = Product.objects.filter(
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
        driver = response.meta.get('driver')
        if 'Access Denied' in driver.title:
            item['status'] = 403
            yield item

        if 'urbanoutfitters' in response.url \
                or 'freepeople' in response.url \
                or 'anthropologie' in response.url:
            message = response.css('.c-pwa-product-oos-rec-tray__lead-message::text').get()
            if message and 'This product is no longer available' in message:
                item['status'] = 404
        elif 'bandier' in response.url or 'lolelife' in response.url:
            if '404' in driver.title:
                item['status'] = 404
        elif 'zara' in response.url:
            if 'Search' in driver.title:
                item['status'] = 404
        elif 'pullandbear' in response.url:
            if 'null' in driver.title:
                item['status'] = 404
        elif 'allsaints' in response.url:
            if 'style,any/colour,any/size,any/' in response.url:
                item['status'] = 404
        yield item
