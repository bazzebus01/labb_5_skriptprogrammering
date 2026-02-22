import os, requests, json, re
from flask import Flask, jsonify, Blueprint
from bs4 import BeautifulSoup
import datetime

# Blueprint init
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
    return list_of_links

def dynamic_file_name(category):
    # Creates a JSON file name based on the current category and name
    today = datetime.date.today().strftime('%d%m%y')
    file_name = category + '_' + today + '.json'
    return file_name # Returns 'category_ddmmyy.json' as string

def price_conversion():
    pass

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
# Fetches the book title in a category
def book_name(URL):
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_data = soup_local.find('article', class_='product_pod')
    book_title = book_data.h3.a.get('title')
    return book_title

def book_price():
    pass

# Fetches category URL, then fetches rating and converts it to 0-5/5
def book_rating(url):
    html_code = requests.get(url)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_rating_unconverted = soup_local.find('p', class_='star-rating')['class'][1] # Finds the second class attribute wherever it also contains 'star-rating'
    book_rating = rating_conversion(book_rating_unconverted)
    return book_rating # Returns '0-5/5' as string


#fetches book UPC with the direct url to the book
def book_id(url):
    html_code = requests.get(url)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    product_info = soup_local.find('table', class_='table table-striped') #finds the contents of the product information table
    id = product_info.tr.td.get_text(strip=True) #collects the text in the first row second column
    return id


def gather_book_data():

# need logic to get the direct link to the book for book_id //sebastian
    pass



# --- JSON Handling ---
def load_json_file():
    pass

def save_books_to_json(category): # WILL WORK when gather_book_data() works!! //Ella
    # Saves the book data from a category into a new JSON file
    file_name = dynamic_file_name(category)
    book_data = gather_book_data() # MAY NEED ADJUSTING //Ella
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

# Untested, needs function gather_book_data() to test. Assumes our route category is formatted 'fantasy', 'historical-fiction' etc.
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
    
    with open(file_name, 'r', encoding='utf-8') as json_file: # Should later be load_json_data()
        book_data = json.load(json_file)

    for book in book_data: # Searches for an ID match, returns book information
        if book['id'] == id:
            print('Book found!') # FYI, this only prints to console //Ella
            return jsonify(book)
    
    return jsonify({'error': f'Book with ID/UPC {id} not found.'}), 404



# --- TESTKOD KOMMER EJ VAD MED I FINAL ---
# Testa skriva ut alla titlar på en sida
def print_all_books(URL):
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    books = soup_local.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3')

    list_of_books = []
    for book in range(len(books)):
        book_title = books[book].article.h3.a.get('title')
        print(book_title)

