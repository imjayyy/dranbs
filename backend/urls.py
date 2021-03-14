from django.conf import settings
from django.urls import path

from backend.views import SiteListView, HomePageDataView, CustomAuthToken, ProfileView, UserCreateView, \
    ProfileUpdateView, ProductsByBrandView, ImageView, LogoutView, ToggleFollowBrandView, BrandInfoView, \
    ToggleLoveProduct, MyLovesView, BoardsView, ProductToggleSaveView, BoardsByCreatorView, ProductsByBoardNameView, \
    BoardInfoView, ToggleFollowBoardView, MyFollowingsView, BoardImageView, TicketView

urlpatterns = [
    path('api/sessions', CustomAuthToken.as_view()),
    path('api/auth/logout', LogoutView.as_view()),
    path('api/me', ProfileView.as_view()),
    path('api/users', UserCreateView.as_view()),
    path('api/update-profile', ProfileUpdateView.as_view()),
    path('api/sites', SiteListView.as_view()),
    path('api/homepage-data', HomePageDataView.as_view()),
    path('api/by-brand-name/<name>', ProductsByBrandView.as_view()),
    path('api/toggle-follow-brand', ToggleFollowBrandView.as_view()),
    path('api/brand/<name>', BrandInfoView.as_view()),
    path('api/toggle-love-product', ToggleLoveProduct.as_view()),
    path('api/my-loves', MyLovesView.as_view()),
    path('api/boards', BoardsView.as_view()),
    path('api/boards-by-creator/<username>', BoardsByCreatorView.as_view()),
    path('api/products-by-board-name/<name>', ProductsByBoardNameView.as_view()),
    path('api/toggle-product-saved', ProductToggleSaveView.as_view()),
    path('api/board/<name>', BoardInfoView.as_view()),
    path('api/board/<name>/image', BoardImageView.as_view()),
    path('api/toggle-follow-board', ToggleFollowBoardView.as_view()),
    path('api/my-followings', MyFollowingsView.as_view()),
    path('api/tickets', TicketView.as_view())
]

if settings.DEBUG:
    urlpatterns += [
        path('images/<subdir>/<filename>', ImageView.as_view())
    ]
