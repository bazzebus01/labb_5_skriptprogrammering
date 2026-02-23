import os, requests, json, re
from flask import Flask, jsonify, Blueprint
from bs4 import BeautifulSoup
import datetime

# Blueprint, innit?
books_bp = Blueprint('books_bp', __name__)

# URL things
BASE_URL = "https://books.toscrape.com/"
CATEGORY_URL = None
full_url = f"{BASE_URL}{CATEGORY_URL}"

# Code to get access to the html data
html_for_BASE_URL = requests.get(BASE_URL)
soup = BeautifulSoup(html_for_BASE_URL.text, 'html.parser')



# --- General Tool Functions ---
# Page counter / checker 
def page_turner():
    current_page_html = soup.find('li', class_='current') # Fetches the HTML code
    current_page_text = current_page_html.get_text(strip=True)
    current_page_str = re.findall(r'\b\d+\b', current_page_text) # Seperates the numbers from the text, stores each number as string in a list

    # Converts the page numbers from strings to int
    # Seperates the current page from the total pages
    current_page = int(current_page_str[0])
    total_pages = int(current_page_str[1])
    return current_page, total_pages

# Fetches all links for categories, stores in list
def get_categories():

    ul_element = soup.find('ul', class_='nav nav-list')

    list_of_links = [a['href'] for a in ul_element.find_all('a')]
    list_of_links.pop(0)

    for link in list_of_links:
        print(link)

def dynamic_file_name(category):
    # Creates a TXT file name based on the current category and name
    today = datetime.date.today().strftime('%d%m%y')
    file_name = category + '_' + today + '.json'
    return file_name # Returns 'forex_ddmmyy.json' as string

def price_conversion(book_price):
    today = datetime.date.today().strftime('%d%m%y')
    file_name = 'forex_' + today + '.txt'

    # File handler for value exchange EUR -> SEK
    if not os.path.exists(f'{file_name}'):
        try:
            with open(file_name, 'w', encoding='utf-8') as txt_file:
                txt = requests.get('https://www.forex.se/valuta/eur/').text
                txt_file.write(txt)
        except Exception as err:
            return('Unable to create TXT file.'), err
    try:
        with open(file_name, 'r', encoding='utf-8') as txt_file:
            stock_exchange = txt_file.read() 
    except Exception as err:
        return('Unable to open TXT file.'), err
    
    soup_stock_exchange = BeautifulSoup(stock_exchange, 'html.parser')
    
    eur_to_sek = soup_stock_exchange.find('span', class_='rate-example-list__example-list-item-to').text # Finds the converted price: 1 EUR = XX,XX SEK
    sek_value = re.search(f'[0-9]+,[0-9]+', eur_to_sek).group() # Converts "XX,XX" SEK to "XX,XX"    
    price_converted = round(book_price * float(sek_value.replace(',', '.')), 2) # Calculates price in SEK

    return price_converted

def rating_conversion(book_rating):
    # Book rating conversion table
    rating_conversion = {
        'One': '1/5',
        'Two': '2/5',
        'Three': '3/5',
        'Four': '4/5',
        'Five': '5/5'
    }
    return rating_conversion.get(book_rating) # Returns '0-5/5' as string

# --- Book Fetching !!! ---
# Fetches the book title for a category. Iterates for every book in a different function
def book_name(URL):
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_data = soup_local.find('article', class_='product_pod')
    book_title = book_data.h3.a.get('title')
    print(book_title)

def book_price(URL):
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_site = soup_local.find('article', class_='product_pod').find('h3').find('a', title=True)['href'] # Finds the book site link
    book_site = book_site.replace('../', '')
    book_site_url = f'{BASE_URL}catalogue/{book_site}' # The full URL to an individual book.
    
    html_code = requests.get(book_site_url)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_price = soup_local.find('p', class_='price_color').text
    book_price = book_price.replace('Â£', '') # Hårdkodat //Ella
    book_price = float(book_price) 
    
    converted_book_price = f'{price_conversion(book_price)} SEK'
    print(converted_book_price)
    return converted_book_price

def book_rating(url):
    # Fetches category URL, then fetches rating and converts it to 0-5/5
    html_code = requests.get(url)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_rating_unconverted = soup_local.find('p', class_='star-rating')['class'][1] # Finds the second class attribute wherever it also contains 'star-rating'
    book_rating = rating_conversion(book_rating_unconverted)
    return book_rating # Returns '0-5/5' as string

def book_id(): # Book UPC
    pass

def gather_book_data(URL):
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    books = soup_local.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3') # Fetches the HTML code for all books on the page, stores in a list
    list_of_books = []
    for book in range(len(books)):
        book_title = books[book].article.h3.a.get('title') # Fetches the title for each book, stores in a variable
        price_text = books[book].find('p', class_='price_color').text # Fetches the price text for each book, stores in a variable
        price_unconverted = float(price_text.replace('£', ''))  # Converts the price text to a number, removes the £ symbol
        list_of_books.append({'title': book_title, 'price': price_unconverted}) # Creates a dictionary for each book with the title and price, appends to the list of books

    return list_of_books 
    



# --- JSON Handling ---
def load_json_file(file_name): #checks if file exists, if not creates it and returns empty list
   with open (file_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        return data


def save_books_to_json(category): # WILL WORK when gather_book_data() works!! //Ella
    # Saves the book data from a category into a new JSON file
    file_name = dynamic_file_name(category)
    book_data = gather_book_data # MAY NEED ADJUSTING //Ella
    if not os.path.exists(f'{file_name}.json'):
        try:
            with open(file_name, 'w', encoding='utf-8') as json_file:
                json.dump(book_data, json_file, ensure_ascii=False, indent=4)
            return book_data # Returns all book data as a list with dicts within
        except Exception as err:
            return('Unable to create JSON file.'), err

# --- HTTP Methods ---
# Route krävs, GET
def dynamic_file_name_checker(): # Temp name
    # Ska kolla om lokal json fil finns och ladda den, annars skapa ny med webscraping. Returnerar alla böcker i kategorin.
    # Kolla: Finns kategorin? om ja, Finns den lokalt? om nej, webscrape-a.
    # Hämta sedan info om alla böcker utefter kategorin.
    pass

@books_bp.route('/books/<string:category>/<string:id>', methods=['GET'])
def get_book_by_id(category, id):
    # Fetches a book within a category by ID
    categories = get_categories()
    if not any(f'/{category}_' in link for link in categories): # "If there isn't any '(category)_' in *any* link inside categories"
        return jsonify({'error': f'Category {category} not found.'}), 404    
    
    # Checks for local file, if it doesn't exist it webscrapes and stores the data in a new JSON file
    file_name = dynamic_file_name(category)
    if not os.path.exists(file_name):
        save_books_to_json(category)

    if not os.path.exists(file_name): # Checks again to make sure the file was created correctly
        return jsonify({'error': 'Failed to create JSON file.'}), 500
    
    data = load_json_file(file_name)

    for book in data: # Searches for an ID match, returns book information
        if book['id'] == id:
            print('Book found!') # FYI, this only prints to console //Ella
            return jsonify(book)
    
    return jsonify({'error': f'Book with ID/UPC {id} not found.'}), 404


save_books_to_json('fantasty')
#print(data)

