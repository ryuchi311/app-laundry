#!/usr/bin/env python3
"""
Database initialization script to create tables with approval columns
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

def create_database():
    """Create the database with all necessary tables including approval columns"""
    
    database_path = os.path.join(os.path.dirname(__file__), 'laundry.db')
    
    try:
        # Connect to database (will create if doesn't exist)
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        print("Creating database tables...")
        
        # Create user table with approval columns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(120) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                phone VARCHAR(20),
                role VARCHAR(20) NOT NULL DEFAULT 'employee',
                is_active BOOLEAN NOT NULL DEFAULT 1,
                is_approved BOOLEAN NOT NULL DEFAULT 0,
                approved_by INTEGER,
                approved_at DATETIME,
                date_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (approved_by) REFERENCES user(id)
            )
        ''')
        print("✅ Created user table")
        
        # Create business settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name VARCHAR(200) NOT NULL DEFAULT 'Accio Laundry',
                contact_phone VARCHAR(20),
                contact_email VARCHAR(120),
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(100),
                postal_code VARCHAR(20),
                country VARCHAR(100) DEFAULT 'Philippines',
                currency VARCHAR(10) DEFAULT 'PHP',
                timezone VARCHAR(50) DEFAULT 'Asia/Manila',
                business_hours TEXT,
                date_created DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                date_modified DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created business_settings table")
        
        # Create default super admin user (pre-approved)
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        cursor.execute('''
            INSERT OR IGNORE INTO user (email, password, full_name, phone, role, is_active, is_approved, date_created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'admin@laundry.com',
            hashed_password,
            'System Administrator',  
            '09123456789',
            'super_admin',
            1,  # is_active
            1,  # is_approved (super admin is pre-approved)
            datetime.now()
        ))
        
        if cursor.rowcount > 0:
            print("✅ Created default super admin user")
        else:
            print("Super admin user already exists")
        
        # Create default business settings
        cursor.execute('''
            INSERT OR IGNORE INTO business_settings (business_name, contact_phone, contact_email, address, city, country)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'Accio Laundry',
            '09123456789',
            'admin@laundry.com',
            '123 Laundry Street',
            'Manila',
            'Philippines'
        ))
        
        if cursor.rowcount > 0:
            print("✅ Created default business settings")
        else:
            print("Business settings already exist")
        
        # Commit all changes
        conn.commit()
        
        # Show created user
        cursor.execute("SELECT email, role, is_approved FROM user WHERE email = 'admin@laundry.com'")
        user = cursor.fetchone()
        if user:
            email, role, is_approved = user
            status = "Approved" if is_approved else "Pending"
            print(f"\nDefault user created: {email} ({role}) - {status}")
        
        conn.close()
        
        print(f"\n🎉 Database created successfully at {database_path}!")
        print("You can now start the Flask application.")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    create_database()
