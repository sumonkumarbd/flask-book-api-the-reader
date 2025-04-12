from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import logging
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'jpg', 'jpeg', 'png'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

db = SQLAlchemy(app)

# Create the upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define the PDF model to store metadata in the database
class PDF(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    thumbnail = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    download_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"PDF({self.title}, {self.author})"

    def to_dict(self):
        """Convert the model instance to a dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'thumbnail': self.thumbnail,
            'category': self.category,
            'file_name': self.file_name,
            'description': self.description,
            'upload_date': self.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            'download_count': self.download_count
        }

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

# Error handler for 500
@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# API health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# DOCUMENTATION ENDPOINT
@app.route('/api/docs', methods=['GET'])
def api_docs():
    """Returns API documentation"""
    docs = {
        'api_version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check endpoint',
            'GET /api/pdfs': 'Get all PDFs',
            'GET /api/pdfs/{id}': 'Get PDF by ID',
            'GET /api/pdfs/title/{title}': 'Get PDF by title',
            'GET /api/search?q={query}': 'Search PDFs by title, author, or category',
            'GET /api/category/{category_name}': 'Get PDFs by category',
            'GET /api/author/{author_name}': 'Get PDFs by author',
            'GET /api/stats': 'Get PDF statistics',
            'GET /api/download/{id}': 'Download PDF file',
            'POST /api/upload': 'Upload a new PDF',
            'PUT /api/pdfs/{id}': 'Update PDF metadata',
            'DELETE /api/pdfs/{id}': 'Delete a PDF'
        }
    }
    return jsonify(docs)

# CRUD OPERATIONS

# Create: Upload PDF and metadata
@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    try:
        if 'pdf_file' not in request.files:
            return jsonify({"error": "No PDF file provided"}), 400

        pdf_file = request.files['pdf_file']
        if pdf_file.filename == '':
            return jsonify({"error": "No PDF file selected"}), 400

        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')
        description = request.form.get('description', '')

        if not title or not author or not category:
            return jsonify({"error": "Missing required fields (title, author, category)"}), 400

        if pdf_file and allowed_file(pdf_file.filename):
            # Create a subfolder inside the 'uploads' folder based on the title
            folder_name = secure_filename(title.replace(" ", "_"))
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
                if thumbnail_file.filename != '' and allowed_file(thumbnail_file.filename):
                    thumbnail_filename = secure_filename(thumbnail_file.filename)
                    thumbnail_path = os.path.join(folder_path, thumbnail_filename)
                    thumbnail_file.save(thumbnail_path)
                    # Make the path relative to the upload folder
                    thumbnail_path = os.path.join(folder_name, thumbnail_filename)

            # Save metadata to the database
            new_pdf = PDF(
                title=title,
                author=author,
                thumbnail=thumbnail_path,
                category=category,
                description=description,
                file_name=filename
            )
            db.session.add(new_pdf)
            db.session.commit()

            logger.info(f"PDF '{title}' uploaded successfully by {author}")
            return jsonify({
                "message": "PDF uploaded successfully!",
                "pdf": new_pdf.to_dict()
            }), 201
        
        return jsonify({"error": "Invalid file format"}), 400
    
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to upload PDF: {str(e)}"}), 500

# Read: Get all PDFs
@app.route('/api/pdfs', methods=['GET'])
def get_pdfs():
    try:
        # Add pagination support
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limit per_page to prevent overloading
        if per_page > 100:
            per_page = 100
            
        # Get paginated results
        pagination = PDF.query.paginate(page=page, per_page=per_page, error_out=False)
        
        pdfs = [pdf.to_dict() for pdf in pagination.items]
        
        return jsonify({
            'pdfs': pdfs,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"Error retrieving PDFs: {str(e)}")
        return jsonify({"error": f"Failed to retrieve PDFs: {str(e)}"}), 500

# Read: Get PDF by ID
@app.route('/api/pdfs/<int:pdf_id>', methods=['GET'])
def get_pdf_by_id(pdf_id):
    try:
        pdf = PDF.query.get(pdf_id)
        if not pdf:
            return jsonify({"error": "PDF not found"}), 404
            
        return jsonify(pdf.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving PDF {pdf_id}: {str(e)}")
        return jsonify({"error": f"Failed to retrieve PDF: {str(e)}"}), 500

# Read: Get PDF by title
@app.route('/api/pdfs/title/<string:title>', methods=['GET'])
def get_pdf_by_title(title):
    try:
        pdf = PDF.query.filter_by(title=title).first()
        if not pdf:
            return jsonify({"error": "PDF not found"}), 404
            
        return jsonify(pdf.to_dict())
    except Exception as e:
        logger.error(f"Error retrieving PDF by title '{title}': {str(e)}")
        return jsonify({"error": f"Failed to retrieve PDF: {str(e)}"}), 500

# Update: Update PDF metadata
@app.route('/api/pdfs/<int:pdf_id>', methods=['PUT'])
def update_pdf(pdf_id):
    try:
        pdf = PDF.query.get(pdf_id)
        if not pdf:
            return jsonify({'error': 'PDF not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update fields that are provided
        if 'title' in data:
            pdf.title = data['title']
        if 'author' in data:
            pdf.author = data['author']
        if 'category' in data:
            pdf.category = data['category']
        if 'description' in data:
            pdf.description = data['description']

        db.session.commit()
        logger.info(f"PDF {pdf_id} updated successfully")

        return jsonify({
            'message': 'PDF updated successfully',
            'pdf': pdf.to_dict()
        })
    except Exception as e:
        logger.error(f"Error updating PDF {pdf_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to update PDF: {str(e)}"}), 500

# Delete: Delete PDF
@app.route('/api/pdfs/<int:pdf_id>', methods=['DELETE'])
def delete_pdf(pdf_id):
    try:
        pdf = PDF.query.get(pdf_id)
        if not pdf:
            return jsonify({"error": "PDF not found"}), 404

        # Folder path using the secure title
        folder_name = secure_filename(pdf.title.replace(" ", "_"))
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)

        # Delete PDF file
        pdf_path = os.path.join(folder_path, pdf.file_name)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f"PDF file {pdf_path} deleted")

        # Delete thumbnail if it exists
        if pdf.thumbnail:
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf.thumbnail)
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
                logger.info(f"Thumbnail {thumbnail_path} deleted")

        # Delete the folder if it's now empty
        if os.path.exists(folder_path) and not os.listdir(folder_path):
            os.rmdir(folder_path)
            logger.info(f"Empty folder {folder_path} removed")

        # Delete DB record
        db.session.delete(pdf)
        db.session.commit()
        logger.info(f"PDF {pdf_id} deleted from database")

        return jsonify({"message": f"PDF with ID {pdf_id} deleted successfully."}), 200
    except Exception as e:
        logger.error(f"Error deleting PDF {pdf_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to delete PDF: {str(e)}"}), 500

# SEARCH AND FILTERING OPERATIONS

# Search PDFs by title, author, or category
@app.route('/api/search', methods=['GET'])
def search_pdfs():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
            
        pdfs = PDF.query.filter(
            (PDF.title.like(f'%{query}%')) | 
            (PDF.author.like(f'%{query}%')) | 
            (PDF.category.like(f'%{query}%')) |
            (PDF.description.like(f'%{query}%'))
        ).all()

        if not pdfs:
            return jsonify({'pdfs': [], 'count': 0, 'message': 'No results found'})

        result = [pdf.to_dict() for pdf in pdfs]
        return jsonify({'pdfs': result, 'count': len(result)})
    except Exception as e:
        logger.error(f"Error searching PDFs with query '{query}': {str(e)}")
        return jsonify({"error": f"Search failed: {str(e)}"}), 500

# Get PDFs by category
@app.route('/api/category/<string:category_name>', methods=['GET'])
def get_pdfs_by_category(category_name):
    try:
        pdfs = PDF.query.filter_by(category=category_name).all()
        
        result = [pdf.to_dict() for pdf in pdfs]
        return jsonify({'pdfs': result, 'count': len(result)})
    except Exception as e:
        logger.error(f"Error retrieving PDFs by category '{category_name}': {str(e)}")
        return jsonify({"error": f"Failed to retrieve PDFs: {str(e)}"}), 500

# Get PDFs by author
@app.route('/api/author/<string:author_name>', methods=['GET'])
def get_pdfs_by_author(author_name):
    try:
        pdfs = PDF.query.filter_by(author=author_name).all()
        
        result = [pdf.to_dict() for pdf in pdfs]
        return jsonify({'pdfs': result, 'count': len(result)})
    except Exception as e:
        logger.error(f"Error retrieving PDFs by author '{author_name}': {str(e)}")
        return jsonify({"error": f"Failed to retrieve PDFs: {str(e)}"}), 500

# ADDITIONAL FUNCTIONALITY

# Get PDF statistics
@app.route('/api/stats', methods=['GET'])
def get_pdf_stats():
    try:
        total_pdfs = PDF.query.count()
        categories = db.session.query(PDF.category, db.func.count(PDF.id)).group_by(PDF.category).all()
        authors = db.session.query(PDF.author, db.func.count(PDF.id)).group_by(PDF.author).all()
        
        # Get most downloaded PDFs
        most_downloaded = PDF.query.order_by(PDF.download_count.desc()).limit(5).all()
        
        # Get recently added PDFs
        recent_pdfs = PDF.query.order_by(PDF.upload_date.desc()).limit(5).all()
        
        stats = {
            'total_pdfs': total_pdfs,
            'categories': {category: count for category, count in categories},
            'authors': {author: count for author, count in authors},
            'most_downloaded': [pdf.to_dict() for pdf in most_downloaded],
            'recent_uploads': [pdf.to_dict() for pdf in recent_pdfs]
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error retrieving PDF statistics: {str(e)}")
        return jsonify({"error": f"Failed to retrieve statistics: {str(e)}"}), 500

# Download PDF
@app.route('/api/download/<int:pdf_id>', methods=['GET'])
def download_pdf(pdf_id):
    try:
        pdf = PDF.query.get(pdf_id)
        if not pdf:
            return jsonify({"error": "PDF not found"}), 404
            
        # Increment download count
        pdf.download_count += 1
        db.session.commit()
        
        # Folder path using the secure title
        folder_name = secure_filename(pdf.title.replace(" ", "_"))
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
        
        return send_from_directory(
            folder_path, 
            pdf.file_name,
            as_attachment=True,
            download_name=pdf.file_name
        )
    except Exception as e:
        logger.error(f"Error downloading PDF {pdf_id}: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Failed to download PDF: {str(e)}"}), 500

# Get thumbnail
@app.route('/api/thumbnail/<int:pdf_id>', methods=['GET'])
def get_thumbnail(pdf_id):
    try:
        pdf = PDF.query.get(pdf_id)
        if not pdf or not pdf.thumbnail:
            # Return a default thumbnail or 404
            return jsonify({"error": "Thumbnail not found"}), 404
            
        # The thumbnail path stored in the DB should be relative to the upload folder
        return send_from_directory(app.config['UPLOAD_FOLDER'], pdf.thumbnail)
    except Exception as e:
        logger.error(f"Error retrieving thumbnail for PDF {pdf_id}: {str(e)}")
        return jsonify({"error": f"Failed to retrieve thumbnail: {str(e)}"}), 500

# Get categories
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = db.session.query(PDF.category).distinct().all()
        category_list = [category[0] for category in categories]
        return jsonify({'categories': category_list})
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        return jsonify({"error": f"Failed to retrieve categories: {str(e)}"}), 500

# Get authors
@app.route('/api/authors', methods=['GET'])
def get_authors():
    try:
        authors = db.session.query(PDF.author).distinct().all()
        author_list = [author[0] for author in authors]
        return jsonify({'authors': author_list})
    except Exception as e:
        logger.error(f"Error retrieving authors: {str(e)}")
        return jsonify({"error": f"Failed to retrieve authors: {str(e)}"}), 500

# Batch operations (optional)
@app.route('/api/batch/delete', methods=['POST'])
def batch_delete():
    try:
        data = request.get_json()
        if not data or 'ids' not in data:
            return jsonify({"error": "No IDs provided"}), 400
            
        ids = data['ids']
        deleted_count = 0
        
        for pdf_id in ids:
            pdf = PDF.query.get(pdf_id)
            if pdf:
                # Delete file(s) logic similar to delete_pdf endpoint
                folder_name = secure_filename(pdf.title.replace(" ", "_"))
                folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_name)
                
                # Delete PDF file
                pdf_path = os.path.join(folder_path, pdf.file_name)
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                
                # Delete thumbnail if it exists
                if pdf.thumbnail:
                    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf.thumbnail)
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                
                # Delete the folder if it's empty
                if os.path.exists(folder_path) and not os.listdir(folder_path):
                    os.rmdir(folder_path)
                
                # Delete database record
                db.session.delete(pdf)
                deleted_count += 1
        
        db.session.commit()
        logger.info(f"Batch deleted {deleted_count} PDFs")
        
        return jsonify({
            "message": f"Successfully deleted {deleted_count} PDFs",
            "deleted_count": deleted_count
        })
    except Exception as e:
        logger.error(f"Error in batch delete: {str(e)}")
        db.session.rollback()
        return jsonify({"error": f"Batch delete failed: {str(e)}"}), 500

# Initialize the database and run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")
    
    app.run(host='0.0.0.0', port=5000, debug=True)