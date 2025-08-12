import sqlite3
from datetime import datetime

def add_audit_columns():
    conn = sqlite3.connect('instance/laundry.db')
    cursor = conn.cursor()
    
    print("Adding audit columns to order table...")
    
    try:
        # Add audit columns to order table
        cursor.execute('ALTER TABLE [order] ADD COLUMN last_edited_by INTEGER')
        print("✓ Added last_edited_by column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ last_edited_by column already exists")
        else:
            print(f"✗ Error adding last_edited_by: {e}")
    
    try:
        cursor.execute('ALTER TABLE [order] ADD COLUMN last_edited_at DATETIME')
        print("✓ Added last_edited_at column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ last_edited_at column already exists")
        else:
            print(f"✗ Error adding last_edited_at: {e}")
    
    try:
        cursor.execute('ALTER TABLE [order] ADD COLUMN edit_count INTEGER DEFAULT 0')
        print("✓ Added edit_count column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ edit_count column already exists")
        else:
            print(f"✗ Error adding edit_count: {e}")
    
    try:
        cursor.execute('ALTER TABLE [order] ADD COLUMN is_modified BOOLEAN DEFAULT 0')
        print("✓ Added is_modified column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✓ is_modified column already exists")
        else:
            print(f"✗ Error adding is_modified: {e}")
    
    # Create OrderAuditLog table
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id VARCHAR(10) NOT NULL,
                action VARCHAR(20),
                field_changed VARCHAR(50),
                old_value TEXT,
                new_value TEXT,
                changed_by INTEGER NOT NULL,
                changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                FOREIGN KEY (changed_by) REFERENCES user (id)
            )
        ''')
        print("✓ Created order_audit_log table")
    except sqlite3.OperationalError as e:
        print(f"✗ Error creating audit log table: {e}")
    
    conn.commit()
    conn.close()
    print("Database migration completed!")

if __name__ == '__main__':
    add_audit_columns()
