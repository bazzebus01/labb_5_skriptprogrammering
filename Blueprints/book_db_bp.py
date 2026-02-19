import os
import json
import requests
from flask import jsonify, Blueprint
from bs4 import BeautifulSoup

book_file = 'date.json'
book_db_bp = Blueprint('book_db_bp', __name__)


@book_db_bp.route('/Books')
def get_books():
    if os.path.exists(book_file):
        with open(book_file, 'r', encoding='utf-8') as cache_file:
            cache_data = json.load(cache_file)
            source = "local_json_file"
            return jsonify({"data": cache_data, "source": source})
    else:
        cache_data = books_to_scrape()
        source = "live_web_scrape"

        if cache_data:
            webb_scrape_data = []
            soup = BeautifulSoup(cache_data, "html.parser")
            with open(book_file, 'w', encoding='utf-8') as cache_file:
                json.dump(cache_data, cache_file, indent=4, ensure_ascii=False)
                
            category_title = soup.find('div', class_='page-header action').text.strip() # letar kategorititel, kan användas som namn för json fil?
            category_books = soup.find_all('article', class_='product_pod').find_all('a', title=True)['href'] # letar fram alla böcker i kategorin på sidan
            book_links = category_books # tar fram länkarna till böckerna

            for link in book_links:
                    book_response = requests.get(link)
                    if book_response.status_code == 200:
                        book_data = book_response.text
                        book_soup = BeautifulSoup(book_data, 'html.parser')

                        # The individual data for each book is collected here.
                        book_title = book_soup.find('div', class_='col-sm-6 product_main').find('h1').text.strip()
                        book_price = book_soup.find('p', class_='price_color').text.strip() # Regex för att ta bort konstiga siffror behövs här i think
                        book_rating = book_soup.find('p', class_='star-rating') # inuti classen star rating finns en till klass som ger betyg. ingen aning om hur man hämtar ut det och behöver formatteras om
                        book_id = book_soup.find('table', class_='table table-striped').find('tr').find('td').text.strip() # ID = UPC

                        return jsonify({
                            'id': book_id,
                            'title': book_title,
                            'price': book_price,
                            'rating': book_rating
                        })
    with open(book_file, 'w', encoding='utf-8') as cache_file:
        json.dump(webb_scrape_data, cache_file, indent=4, ensure_ascii=False)
    #return jsonify({"data": webb_scrape_data, "source": source})

def books_to_scrape():
    url = "https://books.toscrape.com/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' }
    books = []
    try:
        
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            books = soup.find_all('article', class_='product_pod')
            print(f"Found {len(books)} books on the page.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the page: {e}")
   # response.raise_for_status()  # Kontrollera att förfrågan lyckades

def get_all_books(url):
    url = "https://books.toscrape.com/"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    response.raise_for_status()  # Kontrollera att förfrågan lyckades
    books = BeautifulSoup.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3')
    list_of_books = []
    for book in range(len(books)):
        #book_title = books[book].find('h3').find('a')['title']
        #book_price = books[book].find('p', class_='price_color').text.strip()
       # book_rating = books[book].find('p', class_='star-rating')['class'][1]  # Extract the rating from the class
       # book_link = books[book].find('h3').find('a')['href']
        book_title = books[book].article.h3.a.get('title')
        print(book_title)
       # print(f"Book Title: {book_title}, Price: {book_price}, Rating: {book_rating}, Link: {book_link}")

       # list_of_books.append({
            ##'title': book_title,
            #'price': book_price,
           # 'rating': book_rating,
           # 'link': book_link
       # })
    print(list_of_books)
