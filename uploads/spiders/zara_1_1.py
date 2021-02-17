import time

import scrapy
from django.utils import timezone
from parsel import Selector
from scrapy import signals
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Zara_1_1'  # name_gender_type
    allowed_domains = ['www.zara.com']
    start_urls = [
        'https://www.zara.com/ca/en/woman-new-in-l1180.html?v1=1549286',
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

    def scroll(self, browser, timeout):
        scroll_pause_time = timeout
        position = 0
        step = 1000

        time.sleep(scroll_pause_time)

        while True:
            position = position + step
            browser.execute_script("window.scrollTo(0, {0});".format(position))

            time.sleep(scroll_pause_time)

            document_height = browser.execute_script("return document.body.scrollHeight")
            if document_height < position:
                break

    def parse(self, response, **kwargs):
        options = Options()
        options.headless = True
        browser = webdriver.Firefox(options=options)
        browser.implicitly_wait(30)
        browser.get(response.url)
        try:
            browser.find_element_by_css_selector('.modal__close-button').click()
        except NoSuchElementException:
            print('No close button')
        self.scroll(browser, 1.5)

        scrapy_selector = Selector(text=browser.page_source)
        products = scrapy_selector.css('.product')
        for product in products:
            item = ProductItem()
            name = product.css('span.product-name::text').get()
            if name:
                item['title'] = name.strip()
            else:
                continue
            item['price'] = product.css('span.main-price::attr(data-price)').get()
            image_url = product.css('img.product-media::attr(src)').get()
            if image_url and '/w/' in image_url:
                b = image_url.split('/w/')
                c = b[1].split('/')
                d = "{0}/w/900/{1}".format(b[0], c[1])

                item['image_urls'] = [image_url, d]
            else:
                continue

            product_link = product.css('a.name::attr(href)').get()
            item['product_link'] = product_link
            yield item

        browser.quit()
