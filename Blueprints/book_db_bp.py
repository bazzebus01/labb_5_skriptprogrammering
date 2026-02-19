import os
import json
import requests
from flask import jsonify, Blueprint
from bs4 import BeautifulSoup

BOOK_CACHE_FILE = 'kategorinamn_årmånaddag.json'
book_db_bp = Blueprint('book_db', __name__)

@book_db_bp.route('/Books')
def get_books():
    if os.path.exists(BOOK_CACHE_FILE):
        print("Filen hittad")
        with open(BOOK_CACHE_FILE, 'r', encoding='utf-8') as cache_file:
            cache_data = json.load(cache_file)
            source = "local_json_file"
    else:
        print("Filen hittades inte, hämtar från webben")
        cache_data = scrape_books_to_scrape()
        source = "live_web_scrape"

        if cache_data:
            with open(BOOK_CACHE_FILE, 'w', encoding='utf-8') as cache_file:
                json.dump(cache_data, cache_file, indent=4, ensure_ascii=False)

    return jsonify({
        "provider": "BooksToScrape",
        "source": source,
        "count": len(cache_data),
        "Categories": cache_data
    })


def scrape_books_to_scrape():
    url = "https://books.toscrape.com/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    books = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Hämtar kategorier från sidomenyn
        category_container = soup.find("ul", class_="nav nav-list")

        if category_container:
            links = category_container.find_all("a")

            for link in links:
                title = link.get_text(strip=True)

                if title.lower() == "books":
                    continue

                relative_link = link.get("href")
                full_link = f"https://books.toscrape.com/{relative_link}"

                books.append({
                    "Category": title,
                    "link": full_link
                })

    except requests.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    return books
