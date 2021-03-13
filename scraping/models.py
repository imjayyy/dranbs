import os

from django.contrib import admin
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.html import format_html
from django.views.static import serve
from scrapyd_api import ScrapydAPI

from backend.models import Site
from bigaray.settings.base import BASE_DIR


def scraper_path(instance, filename):
    return "spiders/{0}".format(filename)


def validate_py_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.py']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


class Scraper(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=scraper_path, null=True, validators=[validate_py_extension])
    task_id = models.CharField(null=True, blank=True, max_length=255)

    last_scraped = models.DateTimeField(null=True)

    class Meta:
        ordering = ['site__name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scrapyd = ScrapydAPI("http://localhost:6800")

    def start(self):
        spider_name = "{}_{}_{}".format(self.site.name, self.site.gender, self.site.type)
        self.task_id = self.scrapyd.schedule("default", spider_name)
        self.save()

    def stop(self):
        self.scrapyd.cancel("default", self.task_id)
        self.save()

    def spider_status(self):
        if self.task_id:
            job_status = self.scrapyd.job_status('default', self.task_id)
            return job_status
        else:
            return "-"


@receiver(post_delete, sender=Scraper)
def submission_delete(sender, instance, **kwargs):
    instance.file.delete(False)


def start_selected(modeladmin, request, queryset):
    for obj in queryset:
        obj.start()


start_selected.short_description = "Start"


class ScraperAdmin(admin.ModelAdmin):
    list_display = ('id', 'site', 'file', 'last_scraped', 'spider_status', 'spider_log', 'site_actions',)
    readonly_fields = ('last_scraped', 'spider_status', 'spider_log', 'site_actions',)
    actions = [start_selected]

    def start_scraping(self, request, object_id, *args, **kwargs):
        scraper = self.get_object(request, object_id)
        scraper.start()
        return redirect(request.META['HTTP_REFERER'])

    def stop_scraping(self, request, object_id, *args, **kwargs):
        scraper = self.get_object(request, object_id)
        scraper.stop()
        return redirect(request.META['HTTP_REFERER'])

    def serve_spider_log(self, request, object_id, *args, **kwargs):
        scraper = self.get_object(request, object_id)
        spider_name = "{}_{}_{}".format(scraper.site.name, scraper.site.gender, scraper.site.type)
        task_id = scraper.task_id
        log_path = "{}/logs/default/{}/{}.log".format(BASE_DIR, spider_name, task_id)
        return serve(request, os.path.basename(log_path), os.path.dirname(log_path))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/start/', self.admin_site.admin_view(self.start_scraping),
                 name='scraping_scraper_start'),
            path('<path:object_id>/stop/', self.admin_site.admin_view(self.stop_scraping),
                 name='scraping_scraper_stop'),
            path('<path:object_id>/log/', self.admin_site.admin_view(self.serve_spider_log),
                 name='scraping_scraper_log')
        ]
        return custom_urls + urls

    def site_actions(self, obj):
        return format_html('<a class="el-button" href={}>Start</a><a class="el-button" href={}>Stop</a>',
                           reverse('admin:scraping_scraper_start', kwargs={'object_id': obj.pk}),
                           reverse('admin:scraping_scraper_stop', kwargs={'object_id': obj.pk}),
                           )

    site_actions.short_description = "Change Status"
    site_actions.allow_tags = True

    def spider_log(self, obj):
        if obj.task_id:
            log_path = format_html('<a href="{0}">View Log</a>',
                                   reverse('admin:scraping_scraper_log', kwargs={'object_id': obj.pk})
                                   )
        else:
            log_path = '-'
        return log_path

    spider_log.short_description = "Log"
    spider_log.allow_tags = True


class ProductChecker(models.Model):
    name = models.CharField(max_length=255, null=True, unique=True)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=scraper_path, null=True, validators=[validate_py_extension])
    task_id = models.CharField(null=True, blank=True, max_length=255)

    last_scraped = models.DateTimeField(null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scrapyd = ScrapydAPI("http://localhost:6800")

    def start(self):
        self.task_id = self.scrapyd.schedule("default", self.name)
        self.save()

    def stop(self):
        self.scrapyd.cancel("default", self.task_id)
        self.save()

    def spider_status(self):
        if self.task_id:
            job_status = self.scrapyd.job_status('default', self.task_id)
            return job_status
        else:
            return "-"


class ProductCheckerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'file', 'last_scraped', 'spider_status', 'spider_log', 'site_actions',)
    readonly_fields = ('last_scraped', 'spider_status', 'spider_log', 'site_actions',)
    actions = [start_selected]

    def start_scraping(self, request, object_id, *args, **kwargs):
        scraper = self.get_object(request, object_id)
        scraper.start()
        return redirect(request.META['HTTP_REFERER'])

    def stop_scraping(self, request, object_id, *args, **kwargs):
        scraper = self.get_object(request, object_id)
        scraper.stop()
        return redirect(request.META['HTTP_REFERER'])

    def serve_spider_log(self, request, object_id, *args, **kwargs):
        scraper = self.get_object(request, object_id)
        task_id = scraper.task_id
        log_path = "{}/logs/default/{}/{}.log".format(BASE_DIR, scraper.name, task_id)
        return serve(request, os.path.basename(log_path), os.path.dirname(log_path))

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/start/', self.admin_site.admin_view(self.start_scraping),
                 name='scraping_checker_start'),
            path('<path:object_id>/stop/', self.admin_site.admin_view(self.stop_scraping),
                 name='scraping_checker_stop'),
            path('<path:object_id>/log/', self.admin_site.admin_view(self.serve_spider_log),
                 name='scraping_checker_log')
        ]
        return custom_urls + urls

    def site_actions(self, obj):
        return format_html('<a class="el-button" href={}>Start</a><a class="el-button" href={}>Stop</a>',
                           reverse('admin:scraping_checker_start', kwargs={'object_id': obj.pk}),
                           reverse('admin:scraping_checker_stop', kwargs={'object_id': obj.pk}),
                           )

    site_actions.short_description = "Change Status"
    site_actions.allow_tags = True

    def spider_log(self, obj):
        if obj.task_id:
            log_path = format_html('<a href="{0}">View Log</a>',
                                   reverse('admin:scraping_checker_log', kwargs={'object_id': obj.pk})
                                   )
        else:
            log_path = '-'
        return log_path

    spider_log.short_description = "Log"
    spider_log.allow_tags = True
