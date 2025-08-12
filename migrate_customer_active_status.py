#!/usr/bin/env python3
"""
Database Migration: Add is_active column to Customer table
This adds the 'is_active' column to existing customers and sets default value to True.
"""

import sqlite3
from datetime import datetime

def migrate_customer_active_status():
    """Add is_active column to Customer table and set defaults"""
    
    # Connect to the database
    try:
        conn = sqlite3.connect('laundry.db')
        cursor = conn.cursor()
        
        print(f"🔧 Starting Customer Active Status Migration - {datetime.now()}")
        print("=" * 60)
        
        # Check if the customer table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer'")
        if not cursor.fetchone():
            print("❌ Customer table not found. Please run the main application first.")
            return False
        
        # Get current table structure
        cursor.execute("PRAGMA table_info(customer)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Current Customer table columns: {', '.join(columns)}")
        
        # Add is_active column if it doesn't exist
        if 'is_active' not in columns:
            print("Adding 'is_active' column to customer table...")
            cursor.execute("ALTER TABLE customer ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✅ Added 'is_active' column")
        else:
            print("✅ 'is_active' column already exists")
        
        # Update existing customers to have active status
        cursor.execute("SELECT COUNT(*) FROM customer")
        customer_count = cursor.fetchone()[0]
        print(f"📊 Found {customer_count} existing customers")
        
        if customer_count > 0:
            # Update any customers without is_active to active
            cursor.execute("UPDATE customer SET is_active = 1 WHERE is_active IS NULL")
            updated_rows = cursor.rowcount
            print(f"✅ Updated {updated_rows} customers to active status")
        
        # Verify the migration
        print("\n🔍 Verifying migration...")
        cursor.execute("PRAGMA table_info(customer)")
        final_columns = cursor.fetchall()
        
        print("\n📋 Final Customer table structure:")
        for col in final_columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULLABLE'} {'DEFAULT: ' + str(col[4]) if col[4] else ''}")
        
        # Show sample customer data
        cursor.execute("SELECT id, full_name, is_active FROM customer ORDER BY id LIMIT 5")
        customers = cursor.fetchall()
        
        if customers:
            print("\n👥 Sample customer data:")
            for customer in customers:
                status = "✅ Active" if customer[2] else "❌ Inactive"
                print(f"   - #{customer[0]}: {customer[1]} - {status}")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Print summary
        print("\n📊 Migration Summary:")
        print("   - Added 'is_active' column with default value True")
        print("   - Set all existing customers to active status")
        print("   - Customers can now be enabled/disabled instead of deleted")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()
            print("🔐 Database connection closed")

if __name__ == "__main__":
    print("🚀 Customer Active Status Migration Tool")
    print("This will add the 'is_active' column to the Customer table")
    print("=" * 60)
    
    # Run the migration
    success = migrate_customer_active_status()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. Test the customer enable/disable functionality")
        print("3. Verify that inactive customers are displayed correctly")
    else:
        print("\n💥 Migration failed. Please check the error messages above.")
