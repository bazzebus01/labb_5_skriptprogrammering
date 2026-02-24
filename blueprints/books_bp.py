import os, requests, json, re
from flask import request, jsonify, Blueprint, render_template
from bs4 import BeautifulSoup
import datetime

# Blueprint init
books_bp = Blueprint('books_bp', __name__, template_folder='templates')

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
    try:
        current_page_html = soup_local.find('li', class_='current') # Fetches the HTML code 
        current_page_text = current_page_html.get_text(strip=True)
        current_page_str = re.findall(r'\b\d+\b', current_page_text) # Seperates the numbers from the text, stores each number as string in a list
    except:
        current_page = 1
        total_pages = 1
        return current_page, total_pages

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
                html_local = requests.get('https://www.forex.se/valuta/eur/')
                soup_local = BeautifulSoup(html_local.text, 'html.parser')
                content = soup_local.find('span', class_='rate-example-list__example-list-item-to') # Finds converted price ONLY in the HTML
                content = str(content) # Converts the BS4 tag to a text string
                txt_file.write(content)
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
    
# --- Book Fetching !!! --- (Create)
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

    return book_title, converted_book_price, book_rating, id

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
        list_of_books = [] #list to hold the dictionaries in.

        #scrape number of pages for the category
        current_page, max_page = page_turner(category_url)
        while current_page <= max_page:
            # different codes depending on what URL stored in category_url
            if max_page > 1:
                if re.search("index.html", category_url):
                    category_url = re.sub("index.html", f"page-{current_page}.html", category_url) #index.html -> page-X.html. used for multi-page category                    
                elif re.search(f"page-{current_page-1}.html", category_url): #runs if the the URL has the same pagenumber as the last ran current_page varibable value
                    category_url = re.sub(f"page-{current_page-1}.html", f"page-{current_page}.html", category_url) #turns the page to the next 1 -> 2

            soup = fetch_html(category_url)
            books_html = soup.find_all('li', class_='col-xs-6 col-sm-4 col-md-3 col-lg-3')

            
            print(category_url)

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
        return list_of_books # WIP
    except Exception as e:
        print("something went wrong!\n",e)

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
# GET
@books_bp.route('/books/<string:category>', methods=['GET'])
def get_all_books_by_cat(category):
    # Fetches all books by category
    categories = get_categories()
    category_part_url = None
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
    return render_template('category_html.html', books=book_data)
        
# GET ID
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
    temp_book_list = [] #needs a list to use html-template
    for book in book_data: # Searches for an ID match, returns book information
        if book['id'] == id:
            print('Book found!')
            temp_book_list.append(book)
            return render_template('category_html.html', books=temp_book_list)    
    return jsonify({'error': f'Book with ID/UPC {id} not found.'}), 404

# POST
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

# PUT
@books_bp.route('/books/<string:category>/<string:id>', methods=['PUT'])
def update_book(category, id):
    # Required fields
    updated_book = request.json
    required_fields = ['title', 'price', 'rating', 'id']
    if not all(field in updated_book for field in required_fields): # Checks if all required fields are present in the request JSON
        return jsonify({'error': 'Missing required fields'})

    # Checks for a valid category link
    categories = get_categories()
    category_part_url = None

    for link in categories:
        if f'/{category}_' in link:
            category_part_url = link
            break
    if category_part_url is None:
        return jsonify({'error': f'Category {category} not found.'}), 404
    
    category_url = BASE_URL + category_part_url # Returns homepage URL + the full category URL (e.g. /category/fantasy_8/index.html)
    
    # Checks for local file, if it doesn't exist it webscrapes and stores the data in a new JSON file
    file_name = dynamic_file_name(category)
    if not os.path.exists(file_name):
        save_books_to_json(category, category_url)

    # Checks again to make sure the file was created correctly
    if not os.path.exists(file_name):
        return jsonify({'error': 'Failed to create JSON file.'}), 500
    
    # Book updating
    book_data = load_json_file(file_name)
    for book in book_data: # Searches for an ID match, updates book based on request
        if book['id'] == id:
            book.update(updated_book) # Updates the correct book
            with open(file_name, 'w') as json_file:
                json.dump(book_data, json_file, indent=4)
            return jsonify({'result': 'Updated', 'Updated book': book}), 201

    return jsonify({'error': f'Book with ID/UPC {id} not found.'}), 404

# Delete book from category
@books_bp.route('/books/<string:category>/<string:id>', methods=['DELETE'])
def delete_book(category, id):
    try:
        file_name = dynamic_file_name(category)#fetches the file name with datatype

        #file doesn't exist
        if not os.path.exists(file_name):
            return jsonify({'message': f'local cache for {category} can not be found'}), 404
        else:
            with open(file_name, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file) #extracts a list of dictionaries (books)
            for book in json_data:
                if book['id'] == id: #if book id match with input id remove book from list
                    json_data.remove(book)

            #overwrite the file with the new list and return a confirmations message
            with open(file_name, 'w', encoding='utf-8') as json_file:
                json.dump(json_data, json_file, ensure_ascii=False, indent=4)
            return jsonify({'message':'book has been removed from cache'})

    except Exception as e:
        return jsonify({'something went wrong':e}), 500


# Delete category
@books_bp.route('/books/<string:category>', methods=['DELETE'])
def delete_category(category):
    file_name = dynamic_file_name(category) # Checks for local file

    if not os.path.exists(file_name):
        return jsonify({'error': f'Category {category} does not exist.'}), 404

    try:
        os.remove(file_name) # Deletes the JSON file associated with the category, effectively "deleting" the category data
    except Exception as e:
        return jsonify({'error': str(e)}), 500 # Returns a 500 Internal Server Error with the exception message if file deletion fails

    return jsonify({
        'message': 'Category deleted successfully',
        'deleted_category': category
    }), 200

# DELETE: All old JSON files for a category
@books_bp.route('/books/delete/<string:category>', methods=['DELETE'])
def delete_old_files(category):
    # Checks for a valid category
    categories = get_categories()
    if not any(f'/{category}_' in link for link in categories):
        return jsonify({'error': f'Category {category} not found.'}), 404
    
    # Finds all JSON files within the category not matching today's date
    file_name = dynamic_file_name(category)
    for json_file in os.listdir('.'):
        if json_file.startswith(f'{category}_') and json_file.endswith('.json') and json_file != file_name:
            os.remove(json_file) # Removes all JSON files for the category not matching today's date
    return jsonify({'result': f'All old files in the category {category} have been deleted.'}), 200