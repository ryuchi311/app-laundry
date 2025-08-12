"""
Migration script to add LaundryStatusHistory table for tracking status changes
"""

import sqlite3
from datetime import datetime

def migrate():
    """Add LaundryStatusHistory table to track status changes with timestamps"""
    try:
        # Connect to database
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()
        
        # Check if laundry_status_history table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='laundry_status_history'")
        if cursor.fetchone():
            print("LaundryStatusHistory table already exists. Migration may have already been run.")
            conn.close()
            return
        
        print("Starting migration: Adding LaundryStatusHistory table...")
        
        # Create LaundryStatusHistory table
        cursor.execute('''
            CREATE TABLE laundry_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                laundry_id VARCHAR(10) NOT NULL,
                old_status VARCHAR(20),
                new_status VARCHAR(20) NOT NULL,
                changed_by INTEGER NOT NULL,
                changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (changed_by) REFERENCES user (id)
            )
        ''')
        print("✓ Created LaundryStatusHistory table")
        
        # Create index for better query performance
        cursor.execute('CREATE INDEX idx_laundry_status_history_laundry_id ON laundry_status_history(laundry_id)')
        cursor.execute('CREATE INDEX idx_laundry_status_history_changed_at ON laundry_status_history(changed_at)')
        print("✓ Created indexes for LaundryStatusHistory table")
        
        # Add current status entries for existing laundries
        print("Adding current status entries for existing laundries...")
        cursor.execute('''
            INSERT INTO laundry_status_history (laundry_id, old_status, new_status, changed_by, changed_at, notes)
            SELECT 
                l.laundry_id,
                NULL as old_status,
                l.status as new_status,
                COALESCE(l.last_edited_by, 1) as changed_by,
                l.date_received as changed_at,
                'Initial status from migration' as notes
            FROM laundry l
            WHERE l.status IS NOT NULL
        ''')
        
        rows_added = cursor.rowcount
        print(f"✓ Added {rows_added} initial status entries")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully")
        
        # Display summary
        print("\n=== Migration Summary ===")
        print("  - Added LaundryStatusHistory table")
        print("  - Created performance indexes")
        print(f"  - Migrated {rows_added} existing laundry statuses")
        print("  - Status changes will now be automatically tracked")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== LaundryStatusHistory Migration Script ===")
    print("This script will add status change tracking to your laundry management system.")
    
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() in ['y', 'yes']:
        migrate()
        print("\nMigration completed! Status changes will now be tracked with timestamps.")
    else:
        print("Migration cancelled.")
