"""
Initialize the database with all tables
"""
from app import create_app, db

def init_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate them (be careful in production!)
        db.drop_all()
        db.create_all()
        print("Database initialized with all tables including the new 'notes' column!")

if __name__ == '__main__':
    init_database()
