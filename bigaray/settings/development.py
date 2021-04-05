from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    '104.248.182.107',
    'dranbs.com',
    '127.0.0.1'
]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'deployphoenix_prod',
        'USER': 'deployphoenix',
        'PASSWORD': '#;rC$3AJHC9~xKh<',
        'HOST': '127.0.0.1',
        'PORT': '5432'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
