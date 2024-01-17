from .base import *

DEBUG = True

ALLOWED_HOSTS = [
    '104.248.182.107',
    'dranbs.com',
    '127.0.0.1',
    'nju.fashion',
    'www.nju.fashion'
]

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'deployphoenix_prod',
#         'USER': 'deployphoenix',
#         'PASSWORD': '#;rC$3AJHC9~xKh<',
#         'HOST': '127.0.0.1',
#         'PORT': '5432'
#     }
# }
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_DATABASE', os.path.join(BASE_DIR, 'postgres')),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
