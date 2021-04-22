import logging
import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.safestring import mark_safe


class UserProfile(models.Model):
    GENDERS = [
        (1, 'Women'),
        (2, 'Men')
    ]
    gender = models.IntegerField(choices=GENDERS, null=True)
    birthday = models.DateField(null=True)

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)

    class Meta:
        db_table = 'profile'


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

    class Meta:
        db_table = 'sites'
        ordering = ['name']

    def __str__(self):
        return '{0} - {1} - {2}'.format(self.display_name, self.get_gender_display(), self.get_type_display())


class Product(models.Model):
    title = models.CharField(max_length=255)
    image_filename = models.CharField(max_length=255, null=True, blank=True)
    price = models.CharField(max_length=255)
    sale_price = models.CharField(max_length=255, null=True, blank=True)
    product_link = models.URLField(unique=True)
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


class BrandFollower(models.Model):
    brand_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'brand_followers'


class ProductLove(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_love'


class Board(models.Model):
    BOARD_TYPES = [
        (1, 'Public'),
        (0, 'Private')
    ]
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    type = models.IntegerField(choices=BOARD_TYPES)
    image_filename = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'boards'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def image_preview(self):
        if self.image_filename:
            return mark_safe('<img src="/images/{0}" width="100" height="150" />'.format(self.image_filename))
        else:
            return ""


class BoardProduct(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = 'board_product'
        ordering = ['-created_at']


class BoardFollower(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'board_follower'

    def __str__(self):
        return self.board.name


class Ticket(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    reply_message = models.TextField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tickets'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def rendered_reply_message(self):
        if self.reply_message:
            return mark_safe(self.reply_message)
        else:
            return "-"
