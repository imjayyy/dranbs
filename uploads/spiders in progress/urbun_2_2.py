import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem
from . import get_scraperapi_url_ultra_premium

class ProductSpider(scrapy.Spider):
    name = 'Urban-outfitters_2_2'  # name_gender_type
    allowed_domains = ['www.urbanoutfitters.com']
    start_urls = [
        'https://www.urbanoutfitters.com/mens-clothing-sale?page=%s' % page for page in range(1, 8)
    ]
    custom_settings = {
        "DOWNLOAD_DELAY": 20
    }
    base_url = "https://www.urbanoutfitters.com"
    for i in range(len(start_urls)):
        start_urls[i] = get_scraperapi_url_ultra_premium(start_urls[i])
    base_url = "https://www.urbanoutfitters.com"

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
        products = response.css('.c-pwa-tile-grid-inner')
        print('lenght -----------------> ', len(products))

        for idx, product in enumerate(products):
            product_link = product.css('a.o-pwa-product-tile__link::attr(href)').get()

            if not product_link:
                continue
            absolute_url = self.base_url + product_link
            # absolute_url = get_scraperapi_url_ultra_premium(absolute_url)
            # yield scrapy.Request(absolute_url, callback=self.parse_product)
            # yield self.parse_product(product)
            item = ProductItem()
            item['product_link'] = absolute_url
            title = product.css('.o-pwa-product-tile__heading::text').get()
            if title:
                item['title'] = title.strip()
            else:
                pass
            price = product.css('span.c-pwa-product-price__current::text').get()
            if price:
                item['price'] = price
            else:
                pass
            hq_image_url = product.css('img.o-pwa-image__img::attr(src)').get()
            if hq_image_url:
                image_url = hq_image_url.replace('wid=683', 'wid=400')
                item['image_urls'] = [image_url, hq_image_url]
            else:
                pass
            
            yield item
