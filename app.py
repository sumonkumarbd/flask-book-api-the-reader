from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello from Flask on Render!"

@app.route('/books', methods=['GET'])
def get_books():
    return jsonify([
        {
            "book_name": "The Alchemist",
            "author_name": "Paulo Coelho",
            "file_name": "https://example.com/book.pdf",
            "cover_photo": "https://example.com/cover.jpg"
        }
    ])

if __name__ == "__main__":
    app.run(debug=True)
