from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data (can be replaced with a database later)
books = [
    {
        'id': 1,
        'title': 'The Great Gatsby',
        'author': 'F. Scott Fitzgerald'
    },
    {
        'id': 2,
        'title': 'To Kill a Mockingbird',
        'author': 'Harper Lee'
    }
]

# Route to get all books
@app.route('/books', methods=['GET'])
def get_books():
    return jsonify({'books': books})

# Route to get a book by its ID
@app.route('/book/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = next((book for book in books if book['id'] == book_id), None)
    if book is None:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify({'book': book})

# Route to add a new book (POST)
@app.route('/book', methods=['POST'])
def add_book():
    new_book = request.get_json()
    new_id = len(books) + 1
    new_book['id'] = new_id
    books.append(new_book)
    return jsonify({'message': 'Book added successfully', 'book': new_book}), 201

if __name__ == '__main__':
    app.run(debug=True)
