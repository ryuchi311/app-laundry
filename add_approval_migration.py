#!/usr/bin/env python3
"""
Migration script to add user approval system columns
"""

import sys
import os
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

app = create_app()

def add_approval_columns():
    """Add approval columns to the user table"""
    
    database_path = os.path.join(os.path.dirname(__file__), 'laundry.db')
    
    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add approval columns if they don't exist
        if 'is_approved' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN is_approved BOOLEAN DEFAULT 0')
            print("Added 'is_approved' column")
        else:
            print("'is_approved' column already exists")
            
        if 'approved_by' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN approved_by INTEGER')
            print("Added 'approved_by' column")
        else:
            print("'approved_by' column already exists")
            
        if 'approved_at' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN approved_at DATETIME')
            print("Added 'approved_at' column")
        else:
            print("'approved_at' column already exists")
        
        # Commit changes
        conn.commit()
        
        # Set existing users as approved (to maintain functionality)
        cursor.execute("UPDATE user SET is_approved = 1 WHERE is_approved IS NULL OR is_approved = 0")
        updated_rows = cursor.rowcount
        print(f"Set {updated_rows} existing users as approved")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def verify_migration():
    """Verify the migration was successful"""
    with app.app_context():
        try:
            # Try to query users with new columns
            users = User.query.all()
            print(f"\n✅ Migration verification successful!")
            print(f"Found {len(users)} users in database")
            
            for user in users:
                approval_status = "Approved" if user.is_approved else "Pending"
                print(f"  - {user.email}: {approval_status}")
                
        except Exception as e:
            print(f"❌ Migration verification failed: {e}")

if __name__ == '__main__':
    print("Starting approval system migration...")
    
    # Add approval columns
    add_approval_columns()
    
    # Verify migration
    verify_migration()
    
    print("\n🎉 Approval system migration completed!")
    print("The system now supports user approval workflow.")
