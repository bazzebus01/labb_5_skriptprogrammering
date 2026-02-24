import os, requests, json, re
from flask import Flask, jsonify, Blueprint
from flask import request
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
def page_turner(category_url):
    html_code = requests.get(category_url)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    current_page_html = soup_local.find('li', class_='current') # Fetches the HTML code 
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


def get_all_books_by_cat(URL): #have all the functions in the same function?? to shorten scrapetime
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_data = soup_local.find('div', class_='product_main')
    book_title = book_data.h1.get_text()
    
    book_rating_unconverted = soup_local.find('p', class_='star-rating')['class'][1] # Finds the second class attribute wherever it also contains 'star-rating'
    book_rating = rating_conversion(book_rating_unconverted)

    product_info = soup_local.find('table', class_='table table-striped') #finds the contents of the product information table
    id = product_info.tr.td.get_text(strip=True) #collects the text in the first row second column

    return book_title, book_rating, id #behöver lägga till price!!!!! //sebastian

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


def gather_book_data(category_url):
    try:
        list_of_books = [] #list to hold all the data from the books in a catagory

        #fetch number of pages
        current_page, max_page = page_turner(category_url)

        while current_page <= max_page:

            # Fetches the HTML code for all books on the page, stores in a list.
            # different codes depending on what URL stored in category_url
            match current_page:
                case 1:
                    html_code = requests.get(category_url)
                    soup_local = BeautifulSoup(html_code.text, 'html.parser')
                    books_html = soup_local.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3') 
                case 2:
                    category_url = category_url[:-10] + (f"page-{current_page}.html")
                    print(category_url)
                    html_code = requests.get(category_url)
                    soup_local = BeautifulSoup(html_code.text, 'html.parser')
                    books_html = soup_local.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3') 
                case _:
                    category_url = category_url[:-11] + (f"page-{current_page}.html")
                    print(category_url)
                    html_code = requests.get(category_url)
                    soup_local = BeautifulSoup(html_code.text, 'html.parser')
                    books_html = soup_local.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3') 
            
            #loops through all the books on ONE page and adds the data to a list of dictionaries.
            for book in books_html:
                books_link = book.div.a.get('href') #gets the link to the book we're looking at in the category
                book_url = f"https://books.toscrape.com/catalogue{books_link[8:]}"
                scraped_book = get_all_books_by_cat(book_url)

                #creates a dictionary and takes the different values from the webscrape
                book_data = {
                    'title': scraped_book[0],
                    'price': book_price(temp_link),
                    'rating': scraped_book[1],
                    'id': scraped_book[2]
                }

                #adds the collected data of A book to a list
                list_of_books.append(book_data) 
                print(f"finished scraping {book_data['title']}")

            print("currently ",len(list_of_books)," books in the list")
            print(f"end of page {current_page}")

            current_page += 1 #changes what page to scrape
            #end of loop
            
    except Exception as e:
        print(e)


# --- JSON Handling ---
def load_json_file(file_name): #checks if file exists, if not creates it and returns empty list
   with open (file_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        return data


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

@books_bp.route('/books/<string:category>', methods=['POST'])
def create_book(category):
    file_name = dynamic_file_name(category) # Checks for local file, if it doesn't exist it webscrapes and stores the data in a new JSON file

    if not os.path.exists(file_name):
        save_books_to_json(category)

    data = load_json_file(file_name)

    new_book = request.json # Expects a JSON object with the same structure as the existing books

    
    required_fields = ['title', 'price', 'rating', 'id']
    if not all(field in new_book for field in required_fields): # Checks if all required fields are present in the request JSON
        return jsonify({'error': 'Missing required fields'}), 400

    data.append(new_book) # Adds the new book to the existing data list

    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    return jsonify(new_book), 201 # Returns the newly created book data as JSON with a 201 Created status code

