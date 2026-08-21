import sys
import os

# Add root folder to sys.path so we can import app and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.user import User

def initialize_database():
    """Drops and re-creates all database tables, and seeds the default admin user."""
    app = create_app()
    with app.app_context():
        print("Initializing database...")
        db.create_all()
        
        # Check if default admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating default operator account (username: admin, password: admin123)...")
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin account created successfully.")
        else:
            print("Admin account already exists.")
            
        print("Database initialization complete.")

if __name__ == '__main__':
    initialize_database()
