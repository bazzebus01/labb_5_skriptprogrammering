import os, requests, json, re
from bs4 import BeautifulSoup
import datetime

# URL things
BASE_URL = "https://books.toscrape.com/"

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
    except: # Runs if the category only has one page
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

    # Removes all old txt forex files
    for txt_file in os.listdir('.'):
        if txt_file.startswith('forex_') and txt_file.endswith('.txt') and txt_file != file_name:
            os.remove(txt_file) # Removes all 'forex_*.txt' not matching today's date

    # File handler for value exchange
    if not os.path.exists(f'{file_name}'):            
        try:
            with open(file_name, 'w', encoding='utf-8') as txt_file:
                html_local = requests.get('https://www.forex.se/valuta/eur/') # Webscrapes conversion from Forex
                soup_local = BeautifulSoup(html_local.text, 'html.parser')
                content = soup_local.find('span', class_='rate-example-list__example-list-item-to') # Finds converted price ONLY in the HTML
                content = str(content) # Converts the BS4 tag to a text string
                txt_file.write(content) # Writes it to a txt file
        except Exception as err:
            return('Unable to create TXT file.'), err
    
    # Opens the txt file and saves it to price_exchange
    try:
        with open(file_name, 'r', encoding='utf-8') as txt_file:
            price_exchange = txt_file.read() 
    except Exception as err:
        return('Unable to open TXT file.'), err
    
    # Parsing
    soup_price_exchange = BeautifulSoup(price_exchange, 'html.parser')
    eur_to_sek = soup_price_exchange.find('span', class_='rate-example-list__example-list-item-to').text # Finds the converted price
    sek_value = re.search(f'[0-9]+,[0-9]+', eur_to_sek).group() # Converts "XX,XX SEK" to "XX,XX"    
    price_converted = round(book_price * float(sek_value.replace(',', '.')), 2) # Calculates price from the book in SEK
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

    return book_title, converted_book_price, book_rating, id


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
        return list_of_books
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