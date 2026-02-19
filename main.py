import os
from flask import jsonify, Flask, request
from bs4 import BeautifulSoup
import requests
import json
from Blueprints.book_db_bp import book_db_bp


app = Flask(__name__)
app.json.ensure_ascii = False
app.register_blueprint(book_db_bp, url_prefix='/get_books')

@app.route('/')
def start():
    return jsonify({
        "message": "Welcome to the API! Use the endpoint /get_books/Books to retrieve book data."
    })

if __name__ == '__main__':
    app.run(debug=True)