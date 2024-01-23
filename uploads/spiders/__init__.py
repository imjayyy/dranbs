APIKEY = 'f52047399471ce896b178ce185b081df'
from urllib.parse import urlencode, quote
from urllib.parse import urlparse, parse_qs


# Encode the jQuery selector
encoded_selector = quote('.c-pwa-form.c-pwa-email-signup.c-pwa-email-signup--footer')

# Use the encoded selector in your code
wait_for_selector_param = f''

def get_scraperapi_url(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY, 'url': url, }
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


def get_scraperapi_url_renderJS(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY, 'url': url, 'render' : 'true'}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url



def get_scraperapi_url_premium(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY, 'premium':'true', 'url': url, }
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url

def get_scraperapi_url_ultra_premium(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY, 'ultra_premium':'true', 'url': url, }
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


def get_scraperapi_url_ultra_premium_renderJS(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY, 'ultra_premium':'true', 'url': url, 'render' : 'true' }
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url



def revert_scrapper_api_url(proxy_url):
    payload_str = proxy_url
    payload = parse_qs(payload_str)
    original_url = payload.get('url', [''])[0]
    return original_url