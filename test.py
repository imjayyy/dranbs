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


base_urls = ['https://www.anthropologie.com/clothing-new-this-week?page=%s' % page for page in range(1, 4)]
start_urls = [get_scraperapi_url(url) for url in base_urls]


url = (revert_scrapper_api_url(start_urls[0]))

parsed = urlparse(url)
# page = (parse_qs(parsed.query))['page'][0]
# r = requests.get(start_urls[0])
def get_scraperapi_url_ultra_premium_renderJS(url, APIKEY=APIKEY):
    payload = {'api_key': APIKEY, 'ultra_premium':'true', 'url': url, 'render' : 'true' }
    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
    return proxy_url


print(get_scraperapi_url_ultra_premium_renderJS('https://bananarepublic.gapcanada.ca/browse/category.do?cid=48422'))


# from bs4 import BeautifulSoup


# r = requests.get(get_scraperapi_url_ultra_premium_renderJS('https://bananarepublic.gapcanada.ca/browse/category.do?cid=48422'))


# if r.status_code == 200:
#     # Parse the HTML content using BeautifulSoup
#     soup = BeautifulSoup(r.content, 'html.parser')

#     # Find all elements with a class starting with 'product-card'
#     # product_card_classes = [c for c in soup.find_all(class_=lambda x: x and x.startswith('product-card'))]
#     product_card_elements  = soup.find_all(class_='product-card')
#     # Print the found classes
#     # for product_card_class in product_card_classes:
#     #     print(product_card_class.get('class'))

#     for product_card in product_card_elements:
#         print(product_card)
#         print( '-----------------------------------------------------------------------------------------------------------')
#                 # Extract information as needed
#         #     # Example: 
#         # title = product_card.find(class_='product-card__name').get_text()
#         #     # Example: 
#         # price = product_card.find(class_='product-card-price').find('div').find('span').find('span').get_text()
#             # Example: image_url = product_card.find('img', class_='product-card__image')['src']
#             # Example: product_link = product_card.find(class_='product-card__link')['href']


# else:
#     print(f"Failed to retrieve the page. Status code: {r.status_code}")
