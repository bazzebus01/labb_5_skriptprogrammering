import os, requests, json
from flask import Flask, jsonify
from bs4 import BeautifulSoup

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
        scraped_data = 1 # scraped_data()
        source = 'live_web_scraping'
        if scraped_data:
            with open(PROGRAM_CACHE_FILE, 'w', encoding='utf-8') as cache_file:
                json.dump(scraped_data, cache_file, ensure_ascii=False, indent=4)
        return jsonify(cache_file) 