from app import app, db

# Create the app context to use db.create_all()
with app.app_context():
    db.create_all()
