import logging
import os

from django.core.management import BaseCommand
from django.db.models import Q

from backend.models import Product


class Command(BaseCommand):
    help = "Find duplicate records and delete"

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        sql = """
            select *
            from products p
                     left join (select product_link, count(*) from products group by product_link having count(*) > 1) p2
                               on p.product_link = p2.product_link
        """
        products = Product.objects.raw(sql)
        for product in products:
            print(product.id)
