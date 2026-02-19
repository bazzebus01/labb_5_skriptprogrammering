import os, requests, json, re
from flask import Flask, jsonify
from bs4 import BeautifulSoup
from datetime import datetime
import time
"""
app = Flask(__name__)
PROGRAM_CACHE_FILE = 'x.json' # WIP

@app.route('/program_cache')
def program_cache():
    if os.path.exists(PROGRAM_CACHE_FILE): # Om filen finns, bör vara datum- och kategori-känsligt
        with open(PROGRAM_CACHE_FILE, 'r', encoding='utf-8') as cache_file:
            data = json.load(cache_file)
            source = 'cached_file' # WIP
        return jsonify(data)
    else: # Live webscraping
        scraped_data = 1 # scraped_data() # WIP
        source = 'live_web_scraping'
        if scraped_data:
            with open(PROGRAM_CACHE_FILE, 'w', encoding='utf-8') as cache_file:
                json.dump(scraped_data, cache_file, ensure_ascii=False, indent=4)
        return jsonify(cache_file) 
"""    

# --- Bazzes kod ---
def get_current_categories(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    ul_element = soup.find('ul', class_='nav nav-list')

    return [a['href'] for a in 
            ul_element.find_all('a')] # Ta bort första instansen? den verkar vara 'books' som inte är en kategori utan alla böcker
# Skulle även behöva ksk både vanlig titel och url-en (precis som den är nu) för att göra dynamisk json


#--- Ellas kod ---
BASE_URL = 'https://books.toscrape.com/'

def get_category_data(category_url): # Baserat på HTTP GET/CRUD som är WIP. Exempel: fantasy, historical_fiction. Bör matcha namnen från hemsidan
    category_title = category_url
    today = datetime.now().strftime('%d%m%y') # Example: 190226
    file_name = f'{category_title}_{today}.json'.replace(' ', '_').lower() # Example: 'fantasy_190226.json'

    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
            source = 'local_db'
        return jsonify({'source': source, 'data': data})

    else:
        all_categories = get_current_categories(BASE_URL)[1:] # Retrieves all categories, starting at 1 because 'books' isn't a category
        matched_url = None # Sets it to None by default
        for url in all_categories:
            href = url.replace('../', '').replace(' ', '_').lower() # Formats the URL
            if category_url in href: # If it finds a match, it will run the remainder of the else statement
                matched_url = BASE_URL + href
                break
        if not matched_url:
            return jsonify({'error': 'Category not found'}), 404
        
        scraped_data = []
        current_page = matched_url

        while current_page: # Loop that continues as long as there is a next page
            response = requests.get(current_page)
            if response.status_code != 200:
                break

            data = response.text
            soup = BeautifulSoup(data, 'html.parser')
            books = soup.find_all('article', class_='product_pod') # Finds all books in the category's current page

            category_title = soup.find('div', class_='page-header action').text.strip() # Finds category title, example 'Fantasy'
            print(f'Fetching category: {category_title}...')

            for book in books:
                rel_link = book.find('a')['href']
                rel_link_formatted = rel_link.replace('../', '').replace('../../', '').replace('../../../', '') # Formats the relative link to work with the base URL
                url = BASE_URL + 'catalogue/' + rel_link_formatted # Dynamic link for each book, needs to be formatted like this to work
                url_response = requests.get(url)
                book_data = url_response.text
                book_soup = BeautifulSoup(book_data, 'html.parser')

                # The individual data for each book is collected here
                book_main = book_soup.find('div', class_='col-sm-6 product_main')
                book_title = book_main.find('h1').text.strip()
                book_price_no_regex = book_soup.find('p', class_='price_color').text.strip()
                book_price = re.sub(r'[^£0-9.]', '', book_price_no_regex) # Regex; removes anything that isn't the £ symbol, numbers, or a dot
                book_rating_letters = book_soup.find('p', class_='star-rating')['class'][1] # Fetches the second class which contains the rating in letters
                book_id = book_soup.find('table', class_='table table-striped').find('tr').find('td').text.strip() # ID = UPC

                book_rating_conversion = { # Conversion table
                    'One': '1/5',
                    'Two': '2/5',
                    'Three': '3/5',
                    'Four': '4/5',
                    'Five': '5/5'
                }
                book_rating = book_rating_conversion.get(book_rating_letters, 'No rating') # Converts the rating from letters to 1-5/5. Defaults to 'No rating' if nothing is found

                scraped_data.append({
                    'id': book_id,
                    'title': book_title,
                    'price': book_price,
                    'rating': book_rating
                })

                # For clarity in output:
                print(f'Fetched book: {book_title}')

            # Page checker
            next_page_link = soup.find('li', class_='next')
            if next_page_link: # If there are more pages in the category
                next_page_link = soup.find('li', class_='next').find('a')['href']
                base_folder = current_page.rsplit('/', 1)[0] + '/' # Removes index.html, page-2.html etc.
                current_page = base_folder + next_page_link # Dynamic link for the next page in the category
            else:
                print(f'Finished fetching category: {category_title}. Saving...')
                current_page = None # Breaks out of the while loop at the last page

            with open(file_name, 'w', encoding='utf-8') as json_file:
                json.dump(scraped_data, json_file, ensure_ascii=False, indent=4)
            print('Saved!')
get_category_data()