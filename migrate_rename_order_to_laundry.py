#!/usr/bin/env python3
"""
Migration script to rename 'order' table to 'laundry' and update references
"""
import sqlite3
import os
from datetime import datetime

def migrate_database():
    db_path = os.path.join('instance', 'laundry.db')
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    # Create backup
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Creating database backup...")
        conn.execute(f"VACUUM main INTO '{backup_path}'")
        print(f"Backup created: {backup_path}")
        
        # Check if order table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order'")
        if not cursor.fetchone():
            print("Order table does not exist. Migration may have already been run.")
            conn.close()
            return
        
        print("Starting migration: Renaming 'order' table to 'laundry'...")
        
        # Rename the table
        cursor.execute("ALTER TABLE 'order' RENAME TO 'laundry'")
        print("✓ Renamed 'order' table to 'laundry'")
        
        # Rename the order_id column to laundry_id
        cursor.execute("""
            ALTER TABLE laundry RENAME COLUMN order_id TO laundry_id
        """)
        print("✓ Renamed 'order_id' column to 'laundry_id'")
        
        # Check if order_audit_log table exists and rename it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='order_audit_log'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE order_audit_log RENAME TO laundry_audit_log")
            print("✓ Renamed 'order_audit_log' table to 'laundry_audit_log'")
            
            # Rename order_id column in audit log table
            cursor.execute("ALTER TABLE laundry_audit_log RENAME COLUMN order_id TO laundry_id")
            print("✓ Renamed 'order_id' column to 'laundry_id' in audit log")
        
        # Update any references in other tables if they exist
        # Update customer table relationships are handled by the foreign key names
        
        # Commit all changes
        conn.commit()
        
        print("Migration completed successfully!")
        print("The following changes were made:")
        print("  - 'order' table → 'laundry' table")
        print("  - 'order_id' column → 'laundry_id' column")
        print("  - 'order_audit_log' table → 'laundry_audit_log' table")
        print(f"  - Database backup saved as: {backup_path}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== Order to Laundry Migration Script ===")
    print("This script will rename the 'order' table to 'laundry' and update column names.")
    
    response = input("Do you want to continue? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        migrate_database()
    else:
        print("Migration cancelled.")
