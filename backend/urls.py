from django.conf import settings
from django.urls import path

from backend.views import SendResetPasswordLink, ProductsView, CustomAuthToken, UserCreateView, \
    ProfileView, ProductsByBrandView, ImageView, LogoutView, ToggleFollowBrandView, BrandInfoView, \
    ToggleLoveProduct, MyLovesView, BoardsView, ProductToggleSaveView, BoardsByUsernameView, ProductsByBoardView, \
    BoardInfoView, ToggleFollowBoardView, MyFollowingsView, BoardImageView, TicketView, EmailPreview, ResetPassword

urlpatterns = [
    path('api/sessions', CustomAuthToken.as_view()),
    path('api/auth/logout', LogoutView.as_view()),
    path('api/users', UserCreateView.as_view()),
    path('api/send-reset-password-link', SendResetPasswordLink.as_view()),
    path('api/reset-password', ResetPassword.as_view()),

    path('api/products', ProductsView.as_view()),
    path('api/products/<name>', ProductsByBrandView.as_view()),
    path('api/products/<username>/<slug>', ProductsByBoardView.as_view()),
    path('api/toggle-love-product', ToggleLoveProduct.as_view()),
    path('api/toggle-product-saved', ProductToggleSaveView.as_view()),

    path('api/brand/<name>', BrandInfoView.as_view()),
    path('api/toggle-follow-brand', ToggleFollowBrandView.as_view()),

    path('api/boards', BoardsView.as_view()),
    path('api/boards/<username>', BoardsByUsernameView.as_view()),
    path('api/board/<username>/<slug>', BoardInfoView.as_view()),
    path('api/board/<username>/<slug>/image', BoardImageView.as_view()),
    path('api/toggle-follow-board', ToggleFollowBoardView.as_view()),

    path('api/profile', ProfileView.as_view()),
    path('api/my-loves', MyLovesView.as_view()),
    path('api/my-followings', MyFollowingsView.as_view()),

    path('api/tickets', TicketView.as_view())
]

if settings.DEBUG:
    urlpatterns += [
        path('images/<subdir>/<filename>', ImageView.as_view()),
        path('emails/<name>', EmailPreview.as_view())
    ]
