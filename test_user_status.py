#!/usr/bin/env python3
"""
Test script for user activation/deactivation functionality
"""

import os
import sqlite3
from datetime import datetime

def test_user_status_management():
    """Test user activation/deactivation functionality"""
    
    db_path = os.path.join('instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    print("🧪 Testing User Status Management")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Show current user status
    cursor.execute("""
        SELECT id, email, full_name, role, is_active, is_approved
        FROM user 
        ORDER BY date_created
    """)
    
    users = cursor.fetchall()
    
    print("📊 Current User Status:")
    print("-" * 50)
    
    for user in users:
        user_id, email, full_name, role, is_active, is_approved = user
        
        active_status = "🟢 Active" if is_active else "🔴 Inactive"
        approval_status = "✅ Approved" if is_approved else ("⏳ Pending" if is_approved is None else "❌ Rejected")
        
        print(f"👤 {email}")
        print(f"   Name: {full_name or 'Not set'}")
        print(f"   Role: {role}")
        print(f"   Status: {active_status}")
        print(f"   Approval: {approval_status}")
        print()
    
    # Count users by status
    cursor.execute("SELECT COUNT(*) FROM user WHERE is_active = 1")
    active_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user WHERE is_active = 0")
    inactive_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'super_admin' AND is_active = 1")
    active_super_admins = cursor.fetchone()[0]
    
    print("📈 Summary:")
    print(f"   🟢 Active Users: {active_count}")
    print(f"   🔴 Inactive Users: {inactive_count}")
    print(f"   👑 Active Super Admins: {active_super_admins}")
    
    # Safety check
    if active_super_admins == 0:
        print("   ⚠️  WARNING: No active Super Admins!")
    elif active_super_admins == 1:
        print("   ⚠️  CAUTION: Only 1 active Super Admin (cannot be deactivated)")
    
    conn.close()

def create_test_inactive_user():
    """Create a test user and make them inactive for testing"""
    
    db_path = os.path.join('instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if test inactive user already exists
    cursor.execute("SELECT id FROM user WHERE email = ?", ('inactive.test@example.com',))
    existing = cursor.fetchone()
    
    if existing:
        print("⚠️ Test inactive user already exists")
        conn.close()
        return
    
    # Create test user (inactive)
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO user (email, password, full_name, role, is_active, is_approved, date_created)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        'inactive.test@example.com',
        'pbkdf2:sha256:600000$test$hash',  # Dummy password hash
        'Inactive Test User',
        'employee',
        0,  # Inactive
        1,  # Approved but inactive
        now
    ))
    
    conn.commit()
    conn.close()
    
    print("✅ Created test inactive user 'inactive.test@example.com'")

if __name__ == "__main__":
    print("🧪 User Status Management Test")
    print("=" * 40)
    
    # Show current status
    test_user_status_management()
    
    print("\n" + "=" * 40)
    print("🔧 Creating test inactive user...")
    create_test_inactive_user()
    
    print("\n" + "=" * 40)
    print("📊 Updated status after creating test user:")
    test_user_status_management()
    
    print("\n🎯 Next Steps to Test:")
    print("1. Log in as Super Admin at http://127.0.0.1:8080")
    print("2. Go to User Management (/admin/users/users)")
    print("3. Look for users with 'Activate' or 'Deactivate' buttons")
    print("4. Try deactivating a regular user")
    print("5. Try activating the inactive test user")
    print("6. Verify inactive users cannot log in")
