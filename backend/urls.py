from django.conf import settings
from django.urls import path

from backend.views import SiteListView, HomePageDataView, CustomAuthToken, ProfileView, MyBrandsView, \
    ToggleUserSiteView, UserCreateView, ProfileUpdateView, ProductsByBrandView, ImageView, LogoutView

urlpatterns = [
    path('api/sessions', CustomAuthToken.as_view()),
    path('api/auth/logout', LogoutView.as_view()),
    path('api/me', ProfileView.as_view()),
    path('api/users', UserCreateView.as_view()),
    path('api/update-profile', ProfileUpdateView.as_view()),
    path('api/sites', SiteListView.as_view()),
    path('api/homepage-data', HomePageDataView.as_view()),
    path('api/my-profiles', MyBrandsView.as_view()),
    path('api/toggle-users-sites', ToggleUserSiteView.as_view()),
    path('api/by-brand-name/<name>', ProductsByBrandView.as_view())
]

if settings.DEBUG:
    urlpatterns += [
        path('images/<subdir>/<filename>', ImageView.as_view())
    ]
