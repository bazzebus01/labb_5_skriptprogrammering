import os, requests, json, re
from flask import Flask, jsonify, Blueprint
from bs4 import BeautifulSoup
from datetime import datetime

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

def price_conversion():
    pass

def rating_conversion():
    pass

# --- Book Fetching !!! ---
# Fetches the book title for a category. Iterates for every book in a different function
def book_name(URL):
    html_code = requests.get(URL)
    soup_local = BeautifulSoup(html_code.text, 'html.parser')

    book_data = soup_local.find('article', class_='product_pod')
    book_title = book_data.h3.a.get('title')
    print(book_title)

def book_price():
    pass

def book_rating():
    pass

def book_id(): # Book UPC
    pass

def gather_book_data():
    pass

# --- JSON Handling ---
def load_json_file():
    pass

def save_books_to_json():
    pass

# --- HTTP Methods ---
# Route krävs, GET
def dynamic_file_name_checker(): # Temp name
    # Ska kolla om lokal json fil finns och ladda den, annars skapa ny med webscraping. Returnerar alla böcker i kategorin.
    # Kolla: Finns kategorin? om ja, Finns den lokalt? om nej, webscrape-a.
    # Hämta sedan info om alla böcker utefter kategorin.
    pass

# Route krävs, GET ID
def dynamic_book_id_checker(): # Temp name
    # Kollar baserat på ID och kategori. Bör också kolla lokalt i första hand, annars webscrape-a.
    # Kolla: Finns kategorin? om ja, Finns den lokalt? om nej, webscrape-a.
    # Hämta sedan info om boken utefter UPC (ID)
    pass






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

print_all_books('https://books.toscrape.com/catalogue/category/books/sequential-art_5/index.html')