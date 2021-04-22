from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db import models
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.utils.decorators import method_decorator
from django.utils.html import format_html
from django.views import View
from django_admin_listfilter_dropdown.filters import DropdownFilter
from rangefilter.filter import DateTimeRangeFilter

from backend.forms import TicketForm
from backend.models import Site, Product, Ticket, UserProfile, \
    BrandFollower, ProductLove, Board, BoardProduct, BoardFollower
from backend.views import ReplyTicket

admin.site.site_title = 'Dranbs Backend'
admin.site.site_header = 'Dranbs Backend'
admin.site.index_title = 'Dranbs Administration'


class Stat(models.Model):
    class Meta:
        managed = False


def average_age():
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT avg(extract(year from now())-extract(year from birthday)) FROM profile")
        row = cursor.fetchone()

    return row


class StatAdminView(View):
    def get(self, request):
        avg_age = average_age()
        avg = 0
        if avg_age[0]:
            avg = round(average_age()[0], 1)

        return render(request, 'stats.html', {
            'avg': avg
        })


@method_decorator(staff_member_required, name='dispatch')
class StatsSummaryView(View):
    def get(self, request):
        men_count = UserProfile.objects.filter(gender=1).count()
        women_count = UserProfile.objects.filter(gender=2).count()
        return JsonResponse({
            'datasets': [
                {
                    'data': [women_count, men_count],
                    'backgroundColor': [
                        'rgb(255, 99, 132)',
                        'rgb(54, 162, 235)'
                    ]
                }
            ],
            'labels': [
                'Women',
                'Men'
            ]
        })


@method_decorator(staff_member_required, name='dispatch')
class StatsDataView(View):
    def post(self, request):
        per_page = int(request.POST.get('length', 25))
        start_index = int(request.POST.get('start', 0))
        keyword = request.POST.get('search[value]', '')
        order_column = int(request.POST.get('order[0][column]', 0))
        order_dir = request.POST.get('order[0][dir]', 'asc')
        if order_column == 0:
            if order_dir == 'asc':
                sites = Site.objects.filter(name__contains=keyword).order_by('name')[
                        start_index:(start_index + per_page)]
            else:
                sites = Site.objects.filter(name__contains=keyword).order_by('-name')[
                        start_index:(start_index + per_page)]
        else:
            if order_dir == 'asc':
                sites = Site.objects.annotate(u_count=Count('usersite')).filter(name__contains=keyword).order_by(
                    'u_count')[start_index:(start_index + per_page)]
            else:
                sites = Site.objects.annotate(u_count=Count('usersite')).filter(name__contains=keyword).order_by(
                    '-u_count')[start_index:(start_index + per_page)]
        site_list = []
        for site in sites:
            site_list.append({
                'name': site.__str__(),
                'count': site.usersite_set.count()
            })

        return JsonResponse({
            'recordsTotal': Site.objects.count(),
            'recordsFiltered': Site.objects.filter(name__contains=keyword).count(),
            'data': site_list
        })


class StatAdmin(admin.ModelAdmin):
    model = Stat

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            path('stats/', StatAdminView.as_view(), name='%s_%s_changelist' % info),
            path('stats_summary', StatsSummaryView.as_view()),
            path('stats_data', StatsDataView.as_view()),
        ]


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'display_name', 'short_url', 'gender', 'type', 'description')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'site', 'title', 'image_preview', 'price', 'sale_price', 'show_product_link',
        'get_gender', 'status', 'inserted_at', 'updated_at')
    search_fields = ('title', 'price', 'sale_price', 'product_link',)
    list_filter = (
        ('inserted_at', DateTimeRangeFilter),
        ('site__name', DropdownFilter),
        ('site__gender', DropdownFilter),
        ('site__type', DropdownFilter),
        ('status', DropdownFilter),
    )
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'birthday',)
    list_filter = ('gender', 'birthday',)


@admin.register(BrandFollower)
class BrandFollowerAdmin(admin.ModelAdmin):
    list_display = ('brand_name', 'user',)
    list_filter = ('brand_name',)


@admin.register(ProductLove)
class ProductLoveAdmin(admin.ModelAdmin):
    list_display = ('user', 'product',)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'type', 'user', 'image_preview', 'created_at', 'updated_at')
    readonly_fields = ('image_preview',)


@admin.register(BoardProduct)
class BoardProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'board', 'product', 'user', 'created_at')


@admin.register(BoardFollower)
class BoardFollowerAdmin(admin.ModelAdmin):
    list_display = ('board', 'user')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'message', 'replied_at', 'created_at',)
    readonly_fields = ('ticket_actions',)
    form = TicketForm
    change_form_template = 'admin/ticket_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/reply', self.admin_site.admin_view(ReplyTicket.as_view()), name='backend_ticket_reply')
        ]
        return custom_urls + urls

    def ticket_actions(self, obj):
        return format_html('<button class="button reply-ticket" type="button">Reply</button>')
