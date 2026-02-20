import os, requests, json, re
from flask import Flask, jsonify, app
from bs4 import BeautifulSoup
from datetime import datetime
from blueprints.books_bp import books_bp

app = Flask(__name__)

app.register_blueprint(books_bp)


# -- PROGRAM EXECUTION DONT TOUCH --
if __name__ == '__main__':
    app.run(debug=True)