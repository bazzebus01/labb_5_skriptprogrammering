import os, requests, json
from flask import Flask, jsonify
from bs4 import BeautifulSoup

def get_category_data():
    if os.path.exists('kategori_årmånaddag.json'): # Structure dynamic name later
        with open('kategori_årmånaddag.json', 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            source = 'local_db'
        return jsonify(data, source) #?????
    else:
        # web scraping request, save to json, return data
        response = requests.get('https://books.toscrape.com/category/books/historical-fiction_4/index.html') # WIP, kategori ej dynamisk, regex?
        if response.status_code == 200:
            scraped_data = [] # här ska allt skit ligga sen
            data = response.text
            soup = BeautifulSoup(data, 'html.parser')

            category_title = soup.find('div', class_='page-header action').text.strip() # letar kategorititel, kan användas som namn för json fil?
            category_books = soup.find_all('article', class_='product_pod').find_all('a', title=True)['href'] # letar fram alla böcker i kategorin på sidan
            book_links = category_books # tar fram länkarna till böckerna

            for page in range('get range of pages here? (WIP)'):
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

                        scraped_data.append({
                            'id': book_id,
                            'title': book_title,
                            'price': book_price,
                            'rating': book_rating
                        })
            with open('kategori_årmånaddag.json', 'w', encoding='utf-8') as json_file: # Dynamisk filnamn, skapa upp nytt ska den göra också
                json.dump(scraped_data, json_file, ensure_ascii=False, indent=4)
            return jsonify(scraped_data, source)


def get_current_categories(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    ul_element = soup.find('ul', class_='nav nav-list')

    return [a['href'] for a in 
            ul_element.find_all('a')]

def print_all_books_in_cat(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    books = soup.find('article', class_='product_pod')

    print(books)


print(print_all_books_in_cat("https://books.toscrape.com/catalogue/category/books/add-a-comment_18/"))


