"""
Database migration script to add audit tracking columns and table
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
        # Check if audit tracking columns exist in Order table
        cursor.execute("PRAGMA table_info('order')")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new audit tracking columns if they don't exist
        new_columns = [
            ('last_edited_by', 'INTEGER'),
            ('last_edited_at', 'DATETIME'),
            ('edit_count', 'INTEGER DEFAULT 0'),
            ('is_modified', 'BOOLEAN DEFAULT 0')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                print(f"Adding '{column_name}' column to Order table...")
                cursor.execute(f"ALTER TABLE 'order' ADD COLUMN {column_name} {column_type}")
                conn.commit()
                print(f"Successfully added '{column_name}' column!")
        
        # Check if OrderAuditLog table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_audit_log'")
        if not cursor.fetchone():
            print("Creating OrderAuditLog table...")
            cursor.execute('''
                CREATE TABLE order_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id VARCHAR(10) NOT NULL,
                    action VARCHAR(20),
                    field_changed VARCHAR(50),
                    old_value TEXT,
                    new_value TEXT,
                    changed_by INTEGER NOT NULL,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    FOREIGN KEY(changed_by) REFERENCES user(id)
                )
            ''')
            conn.commit()
            print("Successfully created OrderAuditLog table!")
        else:
            print("OrderAuditLog table already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
