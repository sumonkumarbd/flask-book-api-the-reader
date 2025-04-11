from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import Flask, render_template
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration for SQLAlchemy and file upload
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'  # SQLite Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'  # Folder to store uploaded PDFs and images
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}  # Allowed file extensions for PDF and thumbnails

db = SQLAlchemy(app)

# Create the upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define the PDF model to store metadata in the database
class PDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)  # Path to thumbnail image
    category = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"PDF({self.title}, {self.author})"


@app.route('/')
def home():
    return render_template('index.html')

# Route for uploading PDF and metadata
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No PDF file provided"}), 400

    pdf_file = request.files['pdf_file']
    title = request.form.get('title')  # Safe access using get()
    author = request.form.get('author')  # Safe access using get()
    thumbnail = request.form.get('thumbnail')  # Thumbnail URL or file path (or None)
    category = request.form.get('category')  # Safe access using get()

    if not title or not author or not category:
        return jsonify({"error": "Missing required fields (title, author, category)"}), 400

    if pdf_file and allowed_file(pdf_file.filename):
        # Create a subfolder inside the 'uploads' folder based on the title
        folder_name = title.replace(" ", "_")  # Replace spaces with underscores in the title
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

        # Create the folder if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # Save the PDF file inside the folder
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(folder_path, filename)
        pdf_file.save(pdf_path)

        # Handle the thumbnail if provided
        thumbnail_path = None
        if 'thumbnail' in request.files:
            thumbnail_file = request.files['thumbnail']
            if allowed_file(thumbnail_file.filename):
                # Secure the filename for the thumbnail
                thumbnail_filename = secure_filename(thumbnail_file.filename)
                thumbnail_path = os.path.join(folder_path, thumbnail_filename)
                thumbnail_file.save(thumbnail_path)

        # Save metadata to the database
        new_pdf = PDF(
            title=title,
            author=author,
            thumbnail=thumbnail_path,  # Save the thumbnail path (or URL)
            category=category,
            file_name=filename  # Store the filename of the PDF
        )
        db.session.add(new_pdf)
        db.session.commit()

        return jsonify({"message": "PDF uploaded successfully!"}), 201

    return jsonify({"error": "Invalid file format"}), 400


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Route to retrieve PDF metadata from the database
@app.route('/pdfs', methods=['GET'])
def get_pdfs():
    pdfs = PDF.query.all()
    pdf_list = []

    for pdf in pdfs:
        pdf_list.append({
            'id': pdf.id,
            'title': pdf.title,
            'author': pdf.author,
            'thumbnail': pdf.thumbnail,
            'category': pdf.category,
            'file_name': pdf.file_name
        })

    return jsonify(pdf_list)


@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_pdf_by_id(id):
    pdf = PDF.query.get(id)

    if not pdf:
        return jsonify({"error": "PDF not found"}), 404

    # Folder path using the title
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf.title)

    # Delete PDF file
    pdf_path = os.path.join(folder_path, pdf.file_name)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    # Delete thumbnail if it exists
    if pdf.thumbnail:
        thumbnail_path = os.path.join(folder_path, os.path.basename(pdf.thumbnail))
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

    # Delete the folder if it's now empty
    if os.path.exists(folder_path) and not os.listdir(folder_path):
        os.rmdir(folder_path)

    # Delete DB record
    db.session.delete(pdf)
    db.session.commit()

    return jsonify({"message": f"PDF with ID {id} deleted successfully."}), 200


@app.route('/update/<int:id>', methods=['PUT'])
def update_pdf(id):
    pdf = PDF.query.get(id)
    if not pdf:
        return jsonify({'error': 'PDF not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    pdf.title = data.get('title', pdf.title)
    pdf.author = data.get('author', pdf.author)
    pdf.category = data.get('category', pdf.category)

    db.session.commit()

    return jsonify({'message': 'PDF updated successfully', 'pdf': {
        'id': pdf.id,
        'title': pdf.title,
        'author': pdf.author,
        'category': pdf.category,
        'file_name': pdf.file_name,
        'thumbnail': pdf.thumbnail
    }})



# Route to search PDFs by title, author, or category
@app.route('/search', methods=['GET'])
def search_pdfs():
    query = request.args.get('q')
    pdfs = PDF.query.filter(
        (PDF.title.like(f'%{query}%')) | 
        (PDF.author.like(f'%{query}%')) | 
        (PDF.category.like(f'%{query}%'))
    ).all()

    if not pdfs:
        return jsonify({'message': 'No results found!'}), 404

    output = []
    for pdf in pdfs:
        pdf_data = {
            'id': pdf.id,
            'title': pdf.title,
            'author': pdf.author,
            'category': pdf.category,
            'file_name': pdf.file_name,
            'thumbnail': pdf.thumbnail
        }
        output.append(pdf_data)

    return jsonify(output)

# Route to get PDFs by category
@app.route('/category/<category_name>', methods=['GET'])
def get_pdfs_by_category(category_name):
    pdfs = PDF.query.filter_by(category=category_name).all()
    
    if not pdfs:
        return jsonify({'message': 'No PDFs found in this category!'}), 404

    output = []
    for pdf in pdfs:
        pdf_data = {
            'id': pdf.id,
            'title': pdf.title,
            'author': pdf.author,
            'category': pdf.category,
            'file_name': pdf.file_name,
            'thumbnail': pdf.thumbnail
        }
        output.append(pdf_data)

    return jsonify(output)

# Route to get PDFs by author
@app.route('/author/<author_name>', methods=['GET'])
def get_pdfs_by_author(author_name):
    pdfs = PDF.query.filter_by(author=author_name).all()
    
    if not pdfs:
        return jsonify({'message': 'No PDFs found by this author!'}), 404

    output = []
    for pdf in pdfs:
        pdf_data = {
            'id': pdf.id,
            'title': pdf.title,
            'author': pdf.author,
            'category': pdf.category,
            'file_name': pdf.file_name,
            'thumbnail': pdf.thumbnail
        }
        output.append(pdf_data)

    return jsonify(output)

# Route to get PDF statistics
@app.route('/stats', methods=['GET'])
def get_pdf_stats():
    total_pdfs = PDF.query.count()
    output = {
        'total_pdfs': total_pdfs
    }
    return jsonify(output)

# Initialize the database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates the database tables if they don't exist
    app.run(debug=True)

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
