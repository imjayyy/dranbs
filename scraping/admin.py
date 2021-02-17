from django.contrib import admin
from scraping.models import Scraper, ScraperAdmin, ProductChecker, ProductCheckerAdmin

admin.site.register(Scraper, ScraperAdmin)
admin.site.register(ProductChecker, ProductCheckerAdmin)