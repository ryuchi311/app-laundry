"""
Migration script to add role-based access control to the User model.
This adds the 'role' and 'is_active' columns to existing users.
"""

import sqlite3
import os

def migrate_user_roles():
    """Add role and is_active columns to User table and set defaults"""
    
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print("Database not found. Please run the application first to create the database.")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if role column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' not in columns:
            print("Adding 'role' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
            print("✓ Added 'role' column")
        else:
            print("✓ 'role' column already exists")
        
        if 'is_active' not in columns:
            print("Adding 'is_active' column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✓ Added 'is_active' column")
        else:
            print("✓ 'is_active' column already exists")
        
        # Set the first user as super admin if no super admin exists
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'super_admin'")
        super_admin_count = cursor.fetchone()[0]
        
        if super_admin_count == 0:
            cursor.execute("SELECT id FROM user ORDER BY id LIMIT 1")
            first_user = cursor.fetchone()
            
            if first_user:
                user_id = first_user[0]
                cursor.execute("UPDATE user SET role = 'super_admin' WHERE id = ?", (user_id,))
                cursor.execute("SELECT full_name, email FROM user WHERE id = ?", (user_id,))
                user_info = cursor.fetchone()
                print(f"✓ Set user '{user_info[0]}' ({user_info[1]}) as Super Administrator")
        
        # Update any users without roles to 'user'
        cursor.execute("UPDATE user SET role = 'user' WHERE role IS NULL OR role = ''")
        
        # Update any users without is_active to active
        cursor.execute("UPDATE user SET is_active = 1 WHERE is_active IS NULL")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully!")
        
        # Show current user roles
        cursor.execute("SELECT full_name, email, role, is_active FROM user ORDER BY id")
        users = cursor.fetchall()
        
        print("\nCurrent users and roles:")
        print("-" * 60)
        for user in users:
            status = "Active" if user[3] else "Inactive"
            role_display = {
                'super_admin': 'Super Administrator',
                'admin': 'Administrator',
                'user': 'User'
            }.get(user[2], 'User')
            print(f"• {user[0]} ({user[1]}) - {role_display} [{status}]")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting User Role Migration...")
    migrate_user_roles()
    print("\n📋 Migration Summary:")
    print("   - Added 'role' column with default value 'user'")
    print("   - Added 'is_active' column with default value True")
    print("   - Set first user as Super Administrator")
    print("   - All existing users are now active by default")
    print("\n✨ Your role-based access control system is ready!")
