"""bigaray URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from bigaray.settings import base

urlpatterns = [
    path(os.getenv('SECRET_ADMIN_URL') + 'admin/', admin.site.urls),
    path('', include('backend.urls'))
]
urlpatterns += static(base.STATIC_URL, document_root=base.STATIC_ROOT)
urlpatterns += static(base.MEDIA_URL, document_root=base.MEDIA_ROOT)
