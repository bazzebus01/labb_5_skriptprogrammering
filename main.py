import os
from flask import jsonify, Flask
from bs4 import BeautifulSoup
import requests
import json
from Blueprints import book_db_bp

app = Flask(__name__)
app.json.ensure_ascii = False
app.register_blueprint(book_db_bp, url_prefix='/get_books')