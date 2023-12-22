from urllib.parse import urlencode
import requests
from urllib.parse import urlencode, urlparse, parse_qs

APIKEY = 'f52047399471ce896b178ce185b081df'


def get_scraperapi_url(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY,  'url': url , 'render' : True}
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


# start_urls = [f'https://www.freepeople.com/sale-all/?page={page}' for page in range(1, 7)]    
# print(start_urls)
# for i in range(len(start_urls)):
#     start_urls[i] = get_scraperapi_url(start_urls[i])

# print(start_urls[0])


payload = {'api_key': APIKEY, 'ultra_premium':'true', 'url': 'https://www.bandier.com/products/cowhide-zipper-pouch-red'}


# r = requests.get()

url = (get_scraperapi_url('https://www.bandier.com/products/the-slim-cuff-pant-25-brown'))

'404 Page Not Found'

def revert_scrapper_api_url(proxy_url):
    payload_str = proxy_url
    payload = parse_qs(payload_str)
    original_url = payload.get('url', [''])[0]
    return original_url


print(revert_scrapper_api_url('http://api.scraperapi.com/?api_key=f52047399471ce896b178ce185b081df&url=https%3A%2F%2Fwww.bandier.com%2Fproducts%2Fkansa-sherpa-belt-bag-black'))