import os

from django.core.management import BaseCommand

from backend.models import Site
from bigaray.settings import base
from scraping.models import Scraper, ProductChecker


class Command(BaseCommand):
    help = "Import spiders from uploads folder."

    def handle(self, *args, **options):
        spiders_dir = base.MEDIA_ROOT + '/spiders'
        for filename in os.listdir(spiders_dir):
            if filename != '__init__.py' and filename != '__pycache__':
                a = filename.replace('.py', '')
                filepath = 'spiders/' + filename
                if 'checker' in a:
                    try:
                        ProductChecker.objects.get(name=a)
                    except ProductChecker.DoesNotExist:
                        ProductChecker.objects.create(name=a, file=filepath)
                else:
                    b = a.capitalize()
                    c = b.split('_')
                    brand_name = c[0]
                    gender = c[1]
                    brand_type = c[2]
                    try:
                        site = Site.objects.get(name=brand_name, gender=int(gender), type=int(brand_type))
                        try:
                            Scraper.objects.get(site=site)
                        except Scraper.DoesNotExist:
                            Scraper.objects.create(site=site, file=filepath)
                    except Site.DoesNotExist:
                        pass
