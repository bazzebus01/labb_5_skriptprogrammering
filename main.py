from flask import Flask, app
from blueprints.books_bp import books_bp

app = Flask(__name__)

app.register_blueprint(books_bp)

# -- ROOT --
@app.route('/', methods=['GET'])
def homepage():
    return 'Ruffel och Boks databas', 200

# -- PROGRAM EXECUTION DONT TOUCH --
if __name__ == '__main__':
    app.run(debug=True)