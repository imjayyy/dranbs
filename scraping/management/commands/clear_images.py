import logging
import os

from django.core.management import BaseCommand
from django.db.models import Q

from backend.models import Product


class Command(BaseCommand):
    help = "Delete products having empty image field"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        for path, subdirs, files in os.walk('/home/deploy/images'):
            for name in files:
                full_path = os.path.join(path, name)
                full_path = full_path.replace('\\', '/')
                image_filename = full_path.split('/home/deploy/images/')[1]
                product_count = Product.objects.filter(
                    Q(image_filename=image_filename) | Q(hq_image_filename=image_filename)).count()
                if product_count == 0:
                    os.remove(full_path)
                    logger.info("Deleted: {0}".format(image_filename))
