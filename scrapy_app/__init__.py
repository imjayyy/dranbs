import os
import sys
import django
import dotenv

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".."))
dotenv.load_dotenv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bigaray.settings.development')
if os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = os.getenv('DJANGO_SETTINGS_MODULE')

django.setup()
