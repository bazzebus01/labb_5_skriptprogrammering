import os
from flask import jsonify, Flask
from bs4 import BeautifulSoup
import requests
import json

app = Flask(__name__)
PROGRAM_CACHE_FILE = 'kategorinamn_årmånaddag.json'

@app.route('/program_cache')
def program_cache():
    if os.path.exists(PROGRAM_CACHE_FILE):
        with open(PROGRAM_CACHE_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify({"error": "Cache file not found"}), 404