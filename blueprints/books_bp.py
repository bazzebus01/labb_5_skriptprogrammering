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

def price_conversion(book_price):
    # Fetches daily value exchange EUR -> SEK and converts book prices
    today = datetime.date.today().strftime('%d%m%y')
    file_name = 'forex_' + today + '.txt'

    # File handler for value exchange
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
    
    # Parsing
    soup_stock_exchange = BeautifulSoup(stock_exchange, 'html.parser')
    
    eur_to_sek = soup_stock_exchange.find('span', class_='rate-example-list__example-list-item-to').text # Finds the converted price: 1 EUR = XX,XX SEK
    sek_value = re.search(f'[0-9]+,[0-9]+', eur_to_sek).group() # Converts "XX,XX SEK" to "XX,XX"    
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

def fetch_html(URL):
    html_code = requests.get(URL)
    soup =BeautifulSoup(html_code.text, 'html.parser')
    return soup
    
# --- Book Fetching !!! ---
def scrape_book(URL): 
    #the scraped html code
    soup = fetch_html(URL)

    #book title 
    book_data = soup.find('div', class_='product_main')
    book_title = book_data.h1.get_text()
    
    #book rating 
    book_rating_unconverted = soup.find('p', class_='star-rating')['class'][1] # Finds the second class attribute wherever it also contains 'star-rating'
    book_rating = rating_conversion(book_rating_unconverted)

    #book ID/UPC 
    product_info = soup.find('table', class_='table table-striped') 
    id = product_info.tr.td.get_text(strip=True) 

    #book price 
    book_price = soup.find('p', class_='price_color').text
    book_price = book_price.replace('Â£', '') # Removes the weird lettering
    book_price = float(book_price)
    converted_book_price = f'{price_conversion(book_price)} SEK'

    return book_title, converted_book_price, book_rating, id #behöver lägga till price!!!!! //sebastian

def gather_book_data(category_url):
    try:
        list_of_books = [] #list to hold the dictionaries in.

        #scrape number of pages for the category
        current_page, max_page = page_turner(category_url)
        while current_page != 2:#current_page != max_page:
            # different codes depending on what URL stored in category_url
            if re.search("index.html", category_url):
                category_url = re.sub("index.html", f"page-{current_page}.html", category_url) #index.html -> page-X.html. used for multi-page category
            elif re.search(f"page-{current_page-1}.html", category_url): #runs if the the URL has the same pagenumber as the last ran current_page varibable value
                category_url = re.sub(f"page-{current_page-1}.html", f"page-{current_page}.html", category_url) #turns the page to the next 1 -> 2

            soup = fetch_html(category_url)
            books_html = soup.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3')

            #loops through all the books on ONE page and adds the data to a list of dictionaries.
            for book in books_html:
                book_link = book.div.a.get('href')
                book_url = f"https://books.toscrape.com/catalogue{book_link.replace("/", "", 2).replace("..", "")}" #creates the link to scrape with, removes the first 2 '/' and all '..' from "../../../book_name"
                scraped_book = scrape_book(book_url)

                #creates a dictionary with the values from the book
                book_data = {
                    'title': scraped_book[0],
                    'price': scraped_book[1],
                    'rating': scraped_book[2],
                    'id': scraped_book[3]
                }

                list_of_books.append(book_data) 

                print(f"finished scraping {book_data['title']}") #for trouble-shooting

            print("currently ",len(list_of_books)," books in the list")
            print(f"end of page {current_page}")
            current_page += 1 #changes what page to scrape
            #end of loop
        return list_of_books
    except Exception as e:
        print(e)
    return list_of_books # WIP

# --- JSON Handling ---
def load_json_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data

def save_books_to_json(category, category_url):
    # Saves the book data from a category into a new JSON file
    file_name = dynamic_file_name(category)
    book_data = gather_book_data(category_url) # WIP
    if not os.path.exists(f'{file_name}.json'):
        try:
            with open(file_name, 'w', encoding='utf-8') as json_file:
                json.dump(book_data, json_file, ensure_ascii=False, indent=4)
            return book_data # Returns all book data as a list with dicts within
        except Exception as err:
            return('Unable to create JSON file.'), err



# --- HTTP Methods ---
# Route krävs, GET
def get_books_by_category(category): # Temp name
    # Ska kolla om lokal json fil finns och ladda den, annars skapa ny med webscraping. Returnerar alla böcker i kategorin.
    # Kolla: Finns kategorin? om ja, Finns den lokalt? om nej, webscrape-a.
    # Hämta sedan info om alla böcker utefter kategorin.

    #attempt 1: //sebastian
    try:
        
        if os.path.exists(f"../{category}_{datetime.datetime.now().strftime('%d%m%y')}"): #if the path with the category input with todays date
            pass 
        else:
            #look if category exist
            #scrape category of books
            pass

    except Exception as e:
        print(e)
        
# Untested, needs function gather_book_data() to test. Assumes our route category is formatted 'fantasy', 'historical-fiction' etc.
@books_bp.route('/books/<string:category>/<string:id>', methods=['GET'])
def get_book_by_id(category, id):
    # Fetches a book within a category by ID
    categories = get_categories()
    category_part_url = None # WIP

    # Checks for a valid category link
    for link in categories:
        if f'/{category}_' in link:
            category_part_url = link
            break
    if category_part_url is None:
        return jsonify({'error': f'Category {category} not found.'}), 404
    
    category_url = BASE_URL + category_part_url
    
    # Checks for local file, if it doesn't exist it webscrapes and stores the data in a new JSON file
    file_name = dynamic_file_name(category)
    if not os.path.exists(file_name):
        save_books_to_json(category, category_url) # WIP

    if not os.path.exists(file_name): # Checks again to make sure the file was created correctly
        return jsonify({'error': 'Failed to create JSON file.'}), 500
    
    book_data = load_json_file(file_name)
    for book in book_data: # Searches for an ID match, returns book information
        if book['id'] == id:
            print('Book found!')
            return jsonify(book)
    
    return jsonify({'error': f'Book with ID/UPC {id} not found.'}), 404
