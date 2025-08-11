#!/usr/bin/env python3
"""
Migration script to add user approval columns to existing database
"""
import sqlite3
import os
from datetime import datetime

def migrate_database():
    # Database path
    db_path = os.path.join('instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"🔄 Migrating database at {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing columns
        columns_to_add = []
        
        if 'is_approved' not in columns:
            columns_to_add.append(('is_approved', 'BOOLEAN DEFAULT 1'))
        
        if 'approved_by' not in columns:
            columns_to_add.append(('approved_by', 'INTEGER'))
            
        if 'approved_at' not in columns:
            columns_to_add.append(('approved_at', 'DATETIME'))
        
        if not columns_to_add:
            print("✅ All approval columns already exist!")
            return True
        
        print(f"📝 Adding columns: {[col[0] for col in columns_to_add]}")
        
        # Add each column
        for column_name, column_def in columns_to_add:
            alter_sql = f"ALTER TABLE user ADD COLUMN {column_name} {column_def}"
            print(f"   Running: {alter_sql}")
            cursor.execute(alter_sql)
        
        # Update existing users to be approved (super admins and existing users)
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0:
            print(f"📊 Found {user_count} existing users")
            
            # Get the first user (should be super admin) to be the approver
            cursor.execute("SELECT id FROM user ORDER BY id LIMIT 1")
            first_user = cursor.fetchone()
            
            if first_user:
                approver_id = first_user[0]
                now = datetime.now().isoformat()
                
                # Approve all existing users
                cursor.execute("""
                    UPDATE user 
                    SET is_approved = 1, 
                        approved_by = ?, 
                        approved_at = ?
                    WHERE is_approved IS NULL OR is_approved = 0
                """, (approver_id, now))
                
                affected_rows = cursor.rowcount
                print(f"✅ Auto-approved {affected_rows} existing users")
        
        # Commit changes
        conn.commit()
        print("🎉 Migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Starting database migration for user approval system...")
    success = migrate_database()
    
    if success:
        print("\n✅ Migration complete! You can now run the application.")
    else:
        print("\n❌ Migration failed! Please check the errors above.")
