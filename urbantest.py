import requests
from bs4 import BeautifulSoup
from uploads.spiders import get_scraperapi_url_urbanoutfitters


class ProductScraper:
    def __init__(self, start_urls):
        self.start_urls = start_urls
        self.base_url = "https://www.urbanoutfitters.com"

    def save_to_file(self, content, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)

    def run(self):
            for start_url in self.start_urls:
                start_url = get_scraperapi_url_urbanoutfitters(start_url)
                response = requests.get(start_url)
                print(response.text)
                if response.status_code == 200:
                    self.save_to_file(response.text, f"page_urban.html")

            with open('page_urban.html', 'r', encoding='utf-8') as file:
                html_content = file.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            products = soup.select('.c-pwa-tile-grid-inner')

            for idx, product in enumerate(products):
                try:
                    product_link = product.select_one('a.c-pwa-link.c-pwa-link--client.o-pwa-product-tile__link')['href']
                    absolute_url = self.base_url + product_link                    
                    product_data = self.parse_product(product)

                    # Do something with product_data (e.g., save to a database or print)
                    print(product_data)
                except Exception as e:
            # else:
                    print(f"Failed to retrieve product data. {e}")

    def parse_product(self, product):
        # response = requests.get(product_url)
        product_data = {}

        soup = product
        try:
            title = soup.select_one('.o-pwa-product-tile__heading')
            if title:
                product_data['title'] = title.get_text(strip=True)

            price = soup.select_one('span.c-pwa-product-price__current')
            if price:
                product_data['price'] = price.get_text(strip=True)

            hq_image_url = soup.select_one('img.o-pwa-image__img')['src']
            image_url = hq_image_url.replace('wid=683', 'wid=400')
            if hq_image_url:
                product_data['image_urls'] = [image_url, hq_image_url]
        except:
            return product_data
        return product_data


# Replace 'your_start_urls_here' with the actual start URLs you want to scrape
start_urls = ['https://www.urbanoutfitters.com/womens-new-arrivals?page=%s' % page for page in range(1, 2)]
scraper = ProductScraper(start_urls)
scraper.run()
