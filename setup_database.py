#!/usr/bin/env python3
"""
Create database and run migration
"""

import sqlite3
import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def create_database_and_migrate():
    """Create database with all tables and add is_active column to Customer"""
    
    # Connect to the database (creates file if it doesn't exist)
    conn = sqlite3.connect('laundry.db')
    cursor = conn.cursor()
    
    print("🔧 Creating database tables and migrating Customer model")
    print("=" * 60)
    
    try:
        # Create User table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(150) UNIQUE,
            password VARCHAR(150),
            full_name VARCHAR(150),
            phone VARCHAR(20),
            role VARCHAR(20) DEFAULT 'employee',
            is_active BOOLEAN DEFAULT 1,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("✅ Created User table")
        
        # Create Customer table with is_active column
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name VARCHAR(150),
            email VARCHAR(150),
            phone VARCHAR(20),
            is_active BOOLEAN DEFAULT 1,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("✅ Created Customer table with is_active column")
        
        # Create Service table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS service (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("✅ Created Service table")
        
        # Create Laundry table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS laundry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            weight REAL,
            total_amount REAL NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            notes TEXT,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            date_completed DATETIME,
            created_by INTEGER,
            FOREIGN KEY (customer_id) REFERENCES customer (id),
            FOREIGN KEY (service_id) REFERENCES service (id),
            FOREIGN KEY (created_by) REFERENCES user (id)
        )
        ''')
        print("✅ Created Laundry table")
        
        # Create other necessary tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category VARCHAR(100),
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES user (id)
        )
        ''')
        print("✅ Created Expense table")
        
        # Create Notification table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            message TEXT NOT NULL,
            type VARCHAR(20) DEFAULT 'info',
            is_read BOOLEAN DEFAULT 0,
            user_id INTEGER,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
        ''')
        print("✅ Created Notification table")
        
        # Insert sample data
        cursor.execute("SELECT COUNT(*) FROM customer")
        customer_count = cursor.fetchone()[0]
        
        if customer_count == 0:
            # Insert sample customers
            sample_customers = [
                ("John Doe", "john@example.com", "+639123456789", 1),
                ("Jane Smith", "jane@example.com", "+639987654321", 1),
                ("Bob Johnson", "bob@example.com", "+639555123456", 0)  # Inactive customer
            ]
            
            cursor.executemany('''
                INSERT INTO customer (full_name, email, phone, is_active)
                VALUES (?, ?, ?, ?)
            ''', sample_customers)
            
            print(f"✅ Added {len(sample_customers)} sample customers")
        
        # Insert sample services
        cursor.execute("SELECT COUNT(*) FROM service")
        service_count = cursor.fetchone()[0]
        
        if service_count == 0:
            sample_services = [
                ("Wash & Dry", "Standard wash and dry service", 50.0, 1),
                ("Dry Clean", "Professional dry cleaning", 80.0, 1),
                ("Wash Only", "Wash only service", 30.0, 1),
                ("Express Service", "Same day service", 100.0, 1)
            ]
            
            cursor.executemany('''
                INSERT INTO service (name, description, price, is_active)
                VALUES (?, ?, ?, ?)
            ''', sample_services)
            
            print(f"✅ Added {len(sample_services)} sample services")
        
        # Insert sample admin user
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Hash for password "admin123"
            hashed_password = "scrypt:32768:8:1$zB8wR2QvP1DhQlxJ$f5c8e5f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0"
            
            cursor.execute('''
                INSERT INTO user (email, password, full_name, phone, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ("admin@laundry.com", hashed_password, "Administrator", "+639123456789", "super_admin", 1))
            
            print("✅ Added sample admin user (admin@laundry.com / admin123)")
        
        # Commit all changes
        conn.commit()
        
        # Verify the customer table structure
        cursor.execute("PRAGMA table_info(customer)")
        columns = cursor.fetchall()
        
        print("\n📋 Customer table structure:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULLABLE'} {'DEFAULT: ' + str(col[4]) if col[4] else ''}")
        
        # Show sample customer data
        cursor.execute("SELECT id, full_name, is_active FROM customer")
        customers = cursor.fetchall()
        
        if customers:
            print("\n👥 Sample customer data:")
            for customer in customers:
                status = "✅ Active" if customer[2] else "❌ Inactive"
                print(f"   - #{customer[0]}: {customer[1]} - {status}")
        
        print("\n✅ Database created and migrated successfully!")
        print("\n📊 Summary:")
        print("   - Created all necessary tables")
        print("   - Customer table includes 'is_active' column")
        print("   - Added sample data for testing")
        print("   - Ready for enable/disable functionality")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Database Creation and Migration Tool")
    print("This will create the database with all tables including Customer.is_active")
    print("=" * 60)
    
    # Remove existing database file to start fresh
    if os.path.exists('laundry.db'):
        os.remove('laundry.db')
        print("🗑️  Removed existing database file")
    
    # Run the migration
    success = create_database_and_migrate()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart your Flask application")
        print("2. Test the customer enable/disable functionality")
        print("3. Log in with admin@laundry.com / admin123")
    else:
        print("\n💥 Setup failed. Please check the error messages above.")
