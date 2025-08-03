"""
Database migration script to add notes column to Order table
"""
import sqlite3
import os

def migrate_database():
    db_path = 'app/laundry.db'
    
    # Check if database exists
    if not os.path.exists(db_path):
        print("Database doesn't exist yet. It will be created with the new schema.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if notes column already exists
        cursor.execute("PRAGMA table_info('order')")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'notes' not in columns:
            print("Adding 'notes' column to Order table...")
            cursor.execute("ALTER TABLE 'order' ADD COLUMN notes TEXT")
            conn.commit()
            print("Successfully added 'notes' column!")
        else:
            print("'notes' column already exists in Order table.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
