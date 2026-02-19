import os
from flask import jsonify, Flask
from bs4 import BeautifulSoup
import requests
import json
app = Flask(__name__)
BOOK_CACHE_FILE = 'kategorinamn_årmånaddag.json'

@app.route('/Books')
def get_books():
    if os.path.exists(BOOK_CACHE_FILE):
        print("Filen hittad")
        with open(BOOK_CACHE_FILE, 'r', encoding='utf-8-sig') as cache_file:
            cache_data = json.load(cache_file)
            source = "local_json_file"

    else: 
        print ("Filen hittades inte, hämtar från webben")
        cache_data = scrape_BooksToScrape()
        source ="live_web_scrape"

        if cache_data:
            with open(BOOK_CACHE_FILE, 'w', encoding='utf-8') as cache_file:
                json.dump(cache_data, cache_file, indent=4, ensure_ascii=False)

        return jsonify({
        "provider": "BooksToScrape",
        "source": source,
        "count": len(cache_data),
        "Categories": cache_data
        })
   
def scrape_BooksToScrape():
    url = "https://books.toscrape.com/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
 
    book = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        div_container = soup.find_all('div', class_='panel-heading-title')
        for div in div_container:
            link_tag = div.find('a')
            if link_tag:
                title = link_tag.get_text(strip=True)
                relative_link = link_tag.get('href')
                full_link = f"https://books.toscrape.com/{relative_link}" if relative_link.startswith('/') else relative_link
            book.append({
                "Book name": title,
                "link": full_link
            })
    except Exception as e:
        print(f"Error processing book: {e}")
    
    return book