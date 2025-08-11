#!/usr/bin/env python3
"""
Standalone migration script to add user approval system columns
"""

import sqlite3
import os

def main():
    # Get database path
    database_path = os.path.join(os.path.dirname(__file__), 'laundry.db')
    
    if not os.path.exists(database_path):
        print(f"Database not found at {database_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        print("Starting approval system migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Current columns: {columns}")
        
        # Add approval columns if they don't exist
        if 'is_approved' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN is_approved BOOLEAN DEFAULT 1')
            print("✅ Added 'is_approved' column")
        else:
            print("'is_approved' column already exists")
            
        if 'approved_by' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN approved_by INTEGER')
            print("✅ Added 'approved_by' column")
        else:
            print("'approved_by' column already exists")
            
        if 'approved_at' not in columns:
            cursor.execute('ALTER TABLE user ADD COLUMN approved_at DATETIME')
            print("✅ Added 'approved_at' column")  
        else:
            print("'approved_at' column already exists")
        
        # Set existing users as approved (default 1 should handle this, but let's be explicit)
        cursor.execute("UPDATE user SET is_approved = 1 WHERE is_approved IS NULL OR is_approved = 0")
        updated_rows = cursor.rowcount
        print(f"✅ Set {updated_rows} existing users as approved")
        
        # Commit changes
        conn.commit()
        
        # Verify columns were added
        cursor.execute("PRAGMA table_info(user)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"New columns: {new_columns}")
        
        # Show user data
        cursor.execute("SELECT id, email, is_approved FROM user")
        users = cursor.fetchall()
        print(f"\nUsers in database:")
        for user_id, email, is_approved in users:
            status = "Approved" if is_approved else "Pending"
            print(f"  - {email}: {status}")
        
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    main()
