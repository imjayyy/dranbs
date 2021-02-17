import json
from urllib.parse import urlparse, parse_qs

import js2xml
import lxml.etree
import scrapy
from django.utils import timezone
from parsel import Selector
from scrapy import signals

from scraping.models import Scraper
from scrapy_app.items import ProductItem


class ProductSpider(scrapy.Spider):
    name = 'Anthropologie_1_1'  # name_gender_type
    allowed_domains = ['www.anthropologie.com']
    base_url = 'https://www.anthropologie.com/shop'
    base_image_url = 'https://s7d5.scene7.com/is/image/Anthropologie'
    start_urls = ['https://www.anthropologie.com/clothing-new-this-week?page=%s' % page for page in range(1, 4)]

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
        url = response.request.url
        parsed = urlparse(url)
        page = (parse_qs(parsed.query))['page'][0]
        javascript = response.css('script::text').get()
        xml = lxml.etree.tostring(js2xml.parse(javascript), encoding='unicode')
        selector = Selector(text=xml)
        assigns = selector.css('assign[operator="="]')
        for assign in assigns:
            initial_state_tag = assign.css('identifier[name="initialState"]')
            if initial_state_tag:
                initial_state = json.loads(assign.css('string::text').get())
                category = initial_state.get('catchall--clothing-new-this-week').get('category')
                tiles = category.get('tileGrid').get('pages').get(page).get('wrapper').get('tiles')
                for product_tile in tiles:
                    product = product_tile.get('product')
                    sku_info = product_tile.get('skuInfo')
                    product_slug = product.get('productSlug')
                    image_slug = product.get('defaultImage')
                    item = ProductItem()
                    image_url = "{0}/{1}?{2}".format(
                        self.base_image_url, image_slug, "$an-category$&qlt=80&fit=constrain"
                    )
                    hq_image_url = "{0}/{1}?{2}".format(
                        self.base_image_url, image_slug, "$a15-pdp-detail-shot$&hei=900&qlt=80&fit=constrain"
                    )
                    item['title'] = product.get('displayName')
                    item['price'] = "${0}".format(sku_info.get('salePriceLow'))
                    item['image_urls'] = [image_url, hq_image_url]
                    item['product_link'] = "{0}/{1}".format(self.base_url, product_slug)
                    yield item
            else:
                continue
