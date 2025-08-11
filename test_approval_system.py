#!/usr/bin/env python3
"""
Test script to demonstrate user approval workflow
"""
import os
import sqlite3
from datetime import datetime

def show_user_approval_status():
    """Show current user approval status"""
    db_path = os.path.join('instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    print("📊 Current User Approval Status")
    print("=" * 50)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all users with approval info
    cursor.execute("""
        SELECT 
            u.id,
            u.email,
            u.full_name,
            u.role,
            u.is_active,
            u.is_approved,
            u.approved_by,
            u.approved_at,
            u.date_created,
            approver.email as approver_email
        FROM user u
        LEFT JOIN user approver ON u.approved_by = approver.id
        ORDER BY u.date_created
    """)
    
    users = cursor.fetchall()
    
    for user in users:
        user_id, email, full_name, role, is_active, is_approved, approved_by, approved_at, date_created, approver_email = user
        
        print(f"\n👤 User ID: {user_id}")
        print(f"   📧 Email: {email}")
        print(f"   👤 Name: {full_name or 'Not set'}")
        print(f"   🏷️ Role: {role}")
        print(f"   🔆 Active: {'Yes' if is_active else 'No'}")
        
        if is_approved:
            status = "✅ APPROVED"
            if approved_by and approver_email:
                status += f" (by {approver_email})"
            if approved_at:
                status += f" on {approved_at[:19]}"
        elif is_approved is None:
            status = "⏳ PENDING APPROVAL"
        else:
            status = "❌ REJECTED"
            if approved_by and approver_email:
                status += f" (by {approver_email})"
        
        print(f"   📋 Status: {status}")
        print(f"   📅 Created: {date_created[:19] if date_created else 'Unknown'}")
    
    # Summary
    cursor.execute("SELECT COUNT(*) FROM user WHERE is_approved = 1")
    approved_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user WHERE is_approved IS NULL")
    pending_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user WHERE is_approved = 0")
    rejected_count = cursor.fetchone()[0]
    
    print("\n📈 Summary:")
    print(f"   ✅ Approved Users: {approved_count}")
    print(f"   ⏳ Pending Users: {pending_count}")
    print(f"   ❌ Rejected Users: {rejected_count}")
    print(f"   📊 Total Users: {approved_count + pending_count + rejected_count}")
    
    conn.close()

def create_test_pending_user():
    """Create a test user that needs approval"""
    db_path = os.path.join('instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if test user already exists
    cursor.execute("SELECT id FROM user WHERE email = ?", ('testuser@example.com',))
    existing = cursor.fetchone()
    
    if existing:
        print("⚠️ Test user already exists")
        conn.close()
        return
    
    # Create test user (pending approval)
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO user (email, password, full_name, role, is_active, is_approved, date_created)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        'testuser@example.com',
        'pbkdf2:sha256:600000$test$hash',  # Dummy password hash
        'Test User',
        'user',
        1,
        None,  # NULL means pending approval
        now
    ))
    
    conn.commit()
    conn.close()
    
    print("✅ Created test user 'testuser@example.com' with pending approval status")

if __name__ == "__main__":
    print("🧪 User Approval System Test")
    print("=" * 40)
    
    # Show current status
    show_user_approval_status()
    
    print("\n" + "=" * 40)
    print("🔧 Creating test pending user...")
    create_test_pending_user()
    
    print("\n" + "=" * 40)
    print("📊 Updated status after creating test user:")
    show_user_approval_status()
    
    print("\n🎯 Next Steps:")
    print("1. Log in as Super Admin at http://127.0.0.1:8080")
    print("2. Go to User Management")
    print("3. You should see the pending user with approval buttons")
    print("4. Test approving or rejecting the test user")
