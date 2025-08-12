#!/usr/bin/env python3
"""
Database migration script to add image_filename column to inventory_item table
"""
import os
import sys
import sqlite3

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from sqlalchemy import text

def migrate_add_image_column():
    """Add image_filename column to InventoryItem table"""
    
    app = create_app()
    with app.app_context():
        try:
            # Check if column already exists
            cursor = db.session.execute(text("PRAGMA table_info(inventory_item)"))
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'image_filename' not in columns:
                print("📸 Adding image_filename column to inventory_item table...")
                
                # Add the column
                db.session.execute(
                    text("ALTER TABLE inventory_item ADD COLUMN image_filename VARCHAR(255)")
                )
                db.session.commit()
                
                print("✅ Successfully added image_filename column!")
            else:
                print("✅ image_filename column already exists!")
                
            # Verify the column was added
            cursor = db.session.execute(text("PRAGMA table_info(inventory_item)"))
            columns = [row[1] for row in cursor.fetchall()]
            print(f"📊 Current columns in inventory_item: {', '.join(columns)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("🔧 Starting database migration for image upload feature...")
    success = migrate_add_image_column()
    
    if success:
        print("🎉 Migration completed successfully!")
        print("📸 You can now upload images for inventory items!")
    else:
        print("💥 Migration failed. Please check the error message above.")
    
    sys.exit(0 if success else 1)
