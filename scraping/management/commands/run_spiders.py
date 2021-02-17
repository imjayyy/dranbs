from django.core.management import BaseCommand

from scraping.models import Scraper


class Command(BaseCommand):
    help = "run all scrapers"

    def handle(self, *args, **options):
        scrapers = Scraper.objects.all()
        for scraper in scrapers:
            scraper.start()
