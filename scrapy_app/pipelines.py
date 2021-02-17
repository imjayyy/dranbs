# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
from io import BytesIO

from PIL import Image
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline, ImageException
from scrapy_selenium import SeleniumRequest

from backend.models import Site, Product


class ProductPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        site_name_gender_type = spider.name
        site_keys = site_name_gender_type.split('_')
        site_name = site_keys[0]
        site_gender = site_keys[1]
        site_type = site_keys[2]
        try:
            site = Site.objects.get(name=site_name, gender=site_gender, type=site_type)
            title = adapter.get('title')
            price = adapter.get('price')
            sale_price = adapter.get('sale_price')
            images = adapter.get('images')
            image_filename = None
            hq_image_filename = None
            if len(images) == 1:
                image_filename = images[0].get('path')
                hq_image_filename = None
            elif len(images) == 2:
                image_filename = images[0].get('path')
                hq_image_filename = images[1].get('path')
            product_link = adapter.get('product_link')
            try:
                product = Product.objects.get(site=site, product_link=product_link)
                product.price = price
                product.sale_price = sale_price
                product.image_filename = image_filename
                product.hq_image_filename = hq_image_filename
                product.product_link = product_link
                product.save()
                print("Product: {} updated.".format(title))
            except Product.DoesNotExist:
                Product.objects.create(
                    title=title,
                    price=price, sale_price=sale_price,
                    image_filename=image_filename, hq_image_filename=hq_image_filename,
                    product_link=product_link, site=site
                )
                print("Product: {} added.".format(title))
            except Product.MultipleObjectsReturned:
                products = Product.objects.filter(site=site, product_link=product_link)
                products.delete()
                print("Multiple object returned and deleted.")
                Product.objects.create(
                    title=title,
                    price=price, sale_price=sale_price,
                    image_filename=image_filename, hq_image_filename=hq_image_filename,
                    product_link=product_link, site=site
                )
                print("Product: {} added.".format(title))
        except Site.DoesNotExist:
            print("{} does not exist".format(site_name_gender_type))
        return item


class ProductUpdatePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        product_link = adapter.get('product_link')
        status = adapter.get('status')
        try:
            products = Product.objects.filter(product_link=product_link)
            if status == 404:
                products.delete()
            else:
                for product in products:
                    product.status = status
                    product.save()
        except Product.DoesNotExist:
            logger = logging.getLogger(__name__)
            logger.warning("Product doesn't exist: {}".format(product_link))
        return item


class ImagesWithSeleniumProxyPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for image_url in item['image_urls']:
            yield SeleniumRequest(url=image_url)

    def get_images(self, response, request, info, **kwargs):
        driver = response.meta['driver']
        image_src = driver.find_element_by_tag_name('img')
        path = self.file_path(request, response=response, info=info)
        orig_image = Image.open(BytesIO(image_src.screenshot_as_png))

        width, height = orig_image.size
        if width < self.min_width or height < self.min_height:
            raise ImageException("Image too small (%dx%d < %dx%d)" %
                                 (width, height, self.min_width, self.min_height))

        image, buf = self.convert_image(orig_image)
        yield path, image, buf

        for thumb_id, size in self.thumbs.items():
            thumb_path = self.thumb_path(request, thumb_id, response=response.meta['screenshot'], info=info)
            thumb_image, thumb_buf = self.convert_image(image, size)
            yield thumb_path, thumb_image, thumb_buf
