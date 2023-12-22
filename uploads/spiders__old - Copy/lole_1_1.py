import scrapy
from django.utils import timezone
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Lole_1_1'  # name_gender_type
    allowed_domains = ['www.lolelife.com']
    base_url = 'https://www.lolelife.com'
    start_urls = [
        'https://www.lolelife.com/women/new-arrivals?page=%s' % page for page in range(1, 9)
    ]

    custom_settings = {
        'ROBOTSTXT_OBEY': False
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
        products = response.css('.cy-product-block')
        for product in products:
            item = ProductItem()
            title = product.css('.title-product > h2::text').get()
            if title:
                item['title'] = title.strip()
            else:
                continue
            product_link = product.css('a::attr(href)').get()
            price = product.css('.amount span:last-child::text').get()
            if price:
                item['price'] = "${0}".format(price)
            else:
                continue
            image_srcset = product.css('img::attr(data-srcset)').get()
            image_urls = image_srcset.split(',')
            image_url = image_urls[0].split(' ')[0].replace('/50/', '/400/')
            hq_image_url = image_url.replace('/400/', '/800/')
            item['image_urls'] = [image_url, hq_image_url]
            item['product_link'] = "{0}{1}".format(self.base_url, product_link)
            yield item
        # with open('lole.html', 'w', encoding='utf8') as html_file:
        #     html_file.write(response.text)
