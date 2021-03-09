from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db import models
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import path
from django.utils.decorators import method_decorator
from django.views import View

from backend.models import Site, Product, SiteAdmin, ProductAdmin, UserProfile, UserProfileAdmin, BrandFollower, \
    BrandFollowerAdmin, ProductLove, ProductLoveAdmin


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


admin.site.site_title = 'Bigaray Backend'
admin.site.site_header = 'Bigaray Backend'
admin.site.index_title = 'Bigaray Administration'

admin.site.register(Site, SiteAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Stat, StatAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BrandFollower, BrandFollowerAdmin)
admin.site.register(ProductLove, ProductLoveAdmin)
