import logging
import os

from django.core.management import BaseCommand
from django.db.models import Q

from backend.models import Product


class Command(BaseCommand):
    help = "Delete products can't find image"

    def handle(self, *args, **options):
        products = Product.objects.all()
        base_path = "/home/deploy/images"
        for product in products:
            image_path = "{}/{}".format(base_path, product.image_filename)
            if not os.path.exists(image_path):
                product.delete()
