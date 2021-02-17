import os
import logging

from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class Site(models.Model):
    GENDERS = [
        (1, 'Women'),
        (2, 'Men')
    ]
    TYPES = [
        (1, 'New'),
        (2, 'Sale')
    ]
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    scrape_url = models.URLField()
    short_url = models.CharField(max_length=255)
    gender = models.IntegerField(choices=GENDERS)
    type = models.IntegerField(choices=TYPES)
    description = models.TextField(blank=True, null=True)
    inserted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ManyToManyField(User, through="UserSite")

    class Meta:
        db_table = 'sites'
        ordering = ['name']

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.display_name, self.get_gender_display(), self.get_type_display())


class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'short_url', 'gender', 'type', 'description')


class Product(models.Model):
    title = models.CharField(max_length=255)
    image_filename = models.CharField(max_length=255, null=True, blank=True)
    price = models.CharField(max_length=255)
    sale_price = models.CharField(max_length=255, null=True, blank=True)
    product_link = models.URLField()
    hq_image_filename = models.CharField(max_length=255, null=True, blank=True)
    status = models.IntegerField(default=200)

    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    inserted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'
        ordering = ['-inserted_at']

    def __str__(self):
        return self.title

    @property
    def image_preview(self):
        if self.image_filename:
            return mark_safe('<img src="/images/{0}" width="100" height="150" />'.format(self.image_filename))
        else:
            return ""


@receiver(post_delete, sender=Product)
def submission_delete(sender, instance, **kwargs):
    logger = logging.getLogger(__name__)

    base_path = "/home/deploy/images"
    image_path = "{}/{}".format(base_path, instance.image_filename)
    hq_image_path = "{}/{}".format(base_path, instance.hq_image_filename)
    if os.path.exists(image_path):
        logger.info('The product image deleted.')
        os.remove(image_path)
    else:
        logger.warning('The product image does not exist.')

    if os.path.exists(hq_image_path):
        logger.info('The product hq image deleted.')
        os.remove(hq_image_path)
    else:
        logger.warning('The product hq image does not exist.')


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'site', 'title', 'image_preview', 'price', 'sale_price', 'show_product_link',
        'get_gender', 'status', 'inserted_at', 'updated_at')
    search_fields = ('title', 'price', 'sale_price', 'product_link',)
    list_filter = ('site', 'site__gender', 'status')
    readonly_fields = ('image_preview',)
    list_per_page = 50

    def image_preview(self, obj):
        return obj.image_preview

    image_preview.short_description = 'Image Preview'
    image_preview.allow_tags = True

    def get_gender(self, obj):
        return obj.site.get_gender_display()

    get_gender.short_description = 'Gender'
    get_gender.admin_order_field = 'site__gender'

    def show_product_link(self, obj):
        return format_html('<a target="_blank" href={}>{}</a>', obj.product_link, obj.product_link)

    show_product_link.allow_tags = True


class UserSite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_site'


class UserSiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'site')


class UserProfile(models.Model):
    GENDERS = [
        (1, 'Women'),
        (2, 'Men')
    ]
    gender = models.IntegerField(choices=GENDERS, null=True)
    birthday = models.DateField(null=True)
    country = models.CharField(max_length=255, null=True, blank=True)

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)

    class Meta:
        db_table = 'profile'


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'birthday', 'country')
    list_filter = ('gender', 'birthday', 'country',)
