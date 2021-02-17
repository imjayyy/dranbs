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
    name = 'Outdoor-voices_2_1'  # name_gender_type
    allowed_domains = ['www.outdoorvoices.com']
    start_urls = [
        'https://www.outdoorvoices.com/collections/shop-man'
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
        step = 300

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
            browser.find_element_by_css_selector('.bx-close').click()
        except NoSuchElementException:
            print('No close button')
        self.scroll(browser, 1)

        # with open('outdoor.html', 'w', encoding='utf8') as html_file:
        #     html_file.write(browser.page_source)

        scrapy_selector = Selector(text=browser.page_source)
        products = scrapy_selector.css('.Collection_item__9VFnN')
        for product in products:
            title = product.css('.ProductListItem_title__1VTnR > a > span:first-child::text').get()
            price = product.css('.ProductListItem_title__1VTnR > a > span:nth-child(2)::text').get()
            image_urls = product.css('img::attr(srcset)').get()
            image_url = image_urls.split(', ')[0]
            product_link = product.css('.ProductListItem_title__1VTnR > a::attr(href)').get()

            if title and price and image_url and product_link:
                item = ProductItem()
                item['title'] = title
                item['price'] = price
                item['image_urls'] = [image_url, image_url]
                item['product_link'] = product_link
                yield item
        browser.quit()

