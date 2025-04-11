from flask import Flask,jsonify

app = Flask(__name__)
@app.route('/')
def home():
    return "Hello From Flask On Render"

@app.route('/books',methode=['GET'])
def get_books():
    # Dummy data
    books = [
        {
            "book_name": "Sample Book",
            "author_name": "Author 1",
            "file_name": "https://yourdomain.com/uploads/book.pdf",
            "cover_photo": "https://yourdomain.com/uploads/cover.jpg"
        }
    ]
    return jsonify(books)


if __name__ == "__main__":
    app.run()