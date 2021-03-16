from django.core.management import BaseCommand
from django.db import connection
from django.utils import timezone

from backend.models import Product


class Command(BaseCommand):
    help = "Today products"

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='brand name')

    def handle(self, *args, **kwargs):
        name = kwargs['name']
        now = timezone.now()
        start_time = now.strftime("'%Y-%m-%d 00:00:00'")
        end_time = now.strftime("'%Y-%m-%d 23:59:59'")
        sql = """
            select count(*) product_count 
            from products p 
                left join sites s on p.site_id = s.id 
            where p.inserted_at between %s and %s and s.name = %s
            """
        with connection.cursor() as cursor:
            cursor.execute(sql, [start_time, end_time, name])
            row = cursor.fetchone()
            print(row[0])
