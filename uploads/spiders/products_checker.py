from datetime import timedelta
from shutil import which

import scrapy
from django.utils import timezone
from scrapy_selenium import SeleniumRequest

from backend.models import Product
from scrapy_app.items import ProductItem
from . import get_scraperapi_url_ultra_premium, get_scraperapi_url, revert_scrapper_api_url


class BrokenLinksSpider(scrapy.Spider):
    name = 'products_checker'
    handle_httpstatus_list = [404]  # Add this line to handle 404 status code

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
                # 'DOWNLOAD_DELAY': 10,
        # 'SELENIUM_DRIVER_NAME': 'firefox',
        # 'SELENIUM_DRIVER_EXECUTABLE_PATH': which('geckodriver'),
        # 'SELENIUM_DRIVER_ARGUMENTS': ['-headless'],
        # 'DOWNLOADER_MIDDLEWARES': {
        #     'scrapy_selenium.SeleniumMiddleware': 800,
        # },
        'ITEM_PIPELINES': {
            'scrapy_app.pipelines.ProductUpdatePipeline': 300,
        }
    }

    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.start_urls = []
        time_threshold = timezone.now() - timedelta(days=0)
        products = Product.objects.filter(
            inserted_at__lt=time_threshold
        ).order_by('inserted_at')
        for product in products:
            if 'freepeople' in product.product_link:
                self.start_urls.append(get_scraperapi_url_ultra_premium(product.product_link))
            else:
                self.start_urls.append(get_scraperapi_url(product.product_link))

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, meta={'url': url})
            # yield SeleniumRequest(url=url)


    def parse(self, response, **kwargs):
        item = ProductItem()
        item['product_link'] = revert_scrapper_api_url(response.meta['url'])
        item['status'] = response.status

        if response.status == 404:
            item['status'] = response.status
            yield item

        if 'Access Denied' in response.text:
            item['status'] = 403
            yield item

        if 'freepeople' in response.url:
            message = response.css('.c-pwa-product-oos-rec-tray__lead-message::text').get()
            if message and 'This product is no longer available' in message:
                item['status'] = 404

        yield item

    # def parse(self, response, **kwargs):
    #     item = ProductItem()
    #     item['product_link'] = response.request.url
    #     item['status'] = response.status
    #     driver = response.meta.get('driver')
    #     if 'Access Denied' in driver.title:
    #         item['status'] = 403
    #         yield item

    #     if 'freepeople' in response.url4:
    #         message = response.css('.c-pwa-product-oos-rec-tray__lead-message::text').get()
    #         if message and 'This product is no longer available' in message:
    #             item['status'] = 404
    #     elif 'bandier' in response.url:
    #         if '404' in driver.title:
    #             item['status'] = 404
    #     yield item
