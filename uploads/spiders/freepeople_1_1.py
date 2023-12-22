import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem
from urllib.parse import urlencode
from . import APIKEY, get_scraperapi_url_ultra_premium


class ProductSpider(scrapy.Spider):
    name = 'Freepeople_1_1'  # name_gender_type
    allowed_domains = ['www.freepeople.com']
    root_url = 'https://www.freepeople.com'
    # root_url = 'api.scraperapi.com'
    # start_urls = [f'http://api.scraperapi.com?api_key={APIKEY}&url=' + 'https://www.freepeople.com/whats-new/?page=1']
    start_urls = [f'https://www.freepeople.com/whats-new/?page={page}' for page in range(1, 4)]
    # start_urls = []
    # start_urls = ['http://api.scraperapi.com?api_key=APIKEY&url=' + url]
    # for pages in range(1,2):
    #     start_urls.append(f'http://api.scraperapi.com?api_key={APIKEY}&url=https://www.freepeople.com/whats-new/?page={str(pages)}')
    
    for i in range(len(start_urls)):
        start_urls[i] = get_scraperapi_url_ultra_premium(start_urls[i])
    # print('start_urls',start_urls)
    # custom_settings = {
    #     "DOWNLOAD_DELAY": 20
    # }
    custom_settings = {
        'USER_AGENT': None,
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

    def parse(self, response, **kwargs):
        products = response.css('.o-pwa-product-tile')
        print('response', response)
        for idx, product in enumerate(products):
            item = ProductItem()
            title = product.css('.o-pwa-product-tile__heading::text').get()
            if title:
                item['title'] = title.strip()
            else:
                continue
            price = product.css('span.c-pwa-product-price__current::text').get()
            if price:
                item['price'] = price
            else:
                continue

            image_src_set = product.css('source::attr(srcset)').get()
            if image_src_set:
                b = image_src_set.split(', ')
                c = b[0].split(' 698w')
                d = b[1].split(' 349w')
                image_url = d[0]
                hq_image_url = c[0]
                item['image_urls'] = [image_url, hq_image_url]
            else:
                continue

            product_link = product.css('.o-pwa-product-tile__link::attr(href)').get()
            item['product_link'] = self.root_url + product_link
            yield item


    # def start_requests(self):
    #     url = 'http://api.scraperapi.com?api_key=be18f8f1662576413a7f9529db48d10d&url=https://www.freepeople.com/whats-new/?page=1'
    #     yield scrapy.Request(url, callback=self.parse, errback=self.handle_error)


    def handle_http_error(self, failure):
        # Log the error or take appropriate action
        request = failure.request
        response = failure.value.response

        if response is not None:
            status = response.status
            self.logger.error(f"HTTP Error {status} for URL: {request.url}")
            print(f"HTTP Error {status} for URL: {request.url}")
        else:
            print(f"Request failed for URL: {request.url}")
            self.logger.error(f"Request failed for URL: {request.url}")

