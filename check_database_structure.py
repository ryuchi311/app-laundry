#!/usr/bin/env python3
"""
Check database structure and fix if needed
"""

import sqlite3
import os

def check_and_fix_database():
    """Check the database structure and fix if needed"""
    
    print("🔍 Checking Database Structure")
    print("=" * 50)
    
    # Check both possible database locations
    db_paths = ['laundry.db', 'instance/laundry.db']
    
    for db_path in db_paths:
        print(f"\n📂 Checking: {db_path}")
        
        if not os.path.exists(db_path):
            print(f"❌ {db_path} does not exist")
            continue
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if customer table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer'")
            if not cursor.fetchone():
                print("❌ Customer table does not exist")
                conn.close()
                continue
            
            print("✅ Customer table exists")
            
            # Check customer table structure
            cursor.execute("PRAGMA table_info(customer)")
            columns = cursor.fetchall()
            
            print(f"\n📋 Current customer table structure in {db_path}:")
            column_names = []
            for col in columns:
                column_names.append(col[1])
                print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULLABLE'} {'DEFAULT: ' + str(col[4]) if col[4] else ''}")
            
            # Check if is_active column exists
            if 'is_active' not in column_names:
                print(f"\n⚠️ is_active column missing in {db_path}! Adding it now...")
                cursor.execute("ALTER TABLE customer ADD COLUMN is_active BOOLEAN DEFAULT 1")
                print("✅ Added is_active column")
                
                # Update any existing customers to be active
                cursor.execute("UPDATE customer SET is_active = 1 WHERE is_active IS NULL")
                updated = cursor.rowcount
                print(f"✅ Set {updated} existing customers to active")
                
                conn.commit()
            else:
                print("✅ is_active column exists")
            
            # Show customer data
            cursor.execute("SELECT id, full_name, is_active FROM customer")
            customers = cursor.fetchall()
            
            print(f"\n👥 Customer data in {db_path} ({len(customers)} customers):")
            for customer in customers:
                status = "✅ Active" if customer[2] else "❌ Inactive"
                print(f"   - #{customer[0]}: {customer[1]} - {status}")
                
            conn.close()
            
        except sqlite3.Error as e:
            print(f"❌ Database error with {db_path}: {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error with {db_path}: {e}")
            continue

if __name__ == "__main__":
    check_and_fix_database()
    
    print("\n✅ Database structure check and fix completed!")
    print("The Flask app should now work properly.")
