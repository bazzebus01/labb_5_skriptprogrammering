import os, requests, json
from flask import Flask, jsonify
from bs4 import BeautifulSoup

#----------------trulsas kod---------------------

def get_current_categories(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    ul_element = soup.find('ul', class_='nav nav-list')

    return [a['href'] for a in 
            ul_element.find_all('a')]

print(get_current_categories("https://books.toscrape.com/index.html"))
