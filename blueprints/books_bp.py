import os, requests, json, re, datetime
from flask import render_template, jsonify, Blueprint, request
from bs4 import BeautifulSoup
from books_functions import *

# Blueprint init
books_bp = Blueprint('books_bp', __name__, template_folder='templates')

# WIP --- Vet ej om detta ska vara kvar?
BASE_URL = "https://books.toscrape.com/"
html_for_BASE_URL = requests.get(BASE_URL)
soup = BeautifulSoup(html_for_BASE_URL.text, 'html.parser')
# WIP --- Vet ej om detta ska vara kvar?

# --- HTTP Methods ---
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
        
@books_bp.route('/books/<string:category>/<string:id>', methods=['GET'])
def get_book_by_id(category, id):
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

    if not os.path.exists(file_name): # Checks again to make sure the file was created correctly
        return jsonify({'error': 'Failed to create JSON file.'}), 500

    book_data = load_json_file(file_name)
    temp_book_list = [] # Needs a list to use html-template
    for book in book_data: # Searches for an ID match, returns book information
        if book['id'] == id:
            print('Book found!')
            temp_book_list.append(book)
            return render_template('category_html.html', books=temp_book_list)
    return jsonify({'error': f'Book with ID/UPC {id} not found.'}), 404

# UPDATE
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


