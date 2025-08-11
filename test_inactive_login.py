#!/usr/bin/env python3
"""
Test inactive user login prevention
"""

import os
import sqlite3
import requests

def test_inactive_user_login():
    """Test that inactive users cannot log in"""
    
    print("🔒 Testing Inactive User Login Prevention")
    print("=" * 50)
    
    # First, let's create a user with a proper password for testing
    db_path = os.path.join('instance', 'laundry.db')
    
    if not os.path.exists(db_path):
        print("❌ Database not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Set a proper password for the inactive test user
    from werkzeug.security import generate_password_hash
    
    hashed_password = generate_password_hash('testpassword123', method='pbkdf2:sha256')
    
    cursor.execute("""
        UPDATE user 
        SET password = ?
        WHERE email = 'inactive.test@example.com'
    """, (hashed_password,))
    
    conn.commit()
    
    # Verify user status
    cursor.execute("""
        SELECT email, is_active, is_approved
        FROM user 
        WHERE email = 'inactive.test@example.com'
    """)
    
    user_data = cursor.fetchone()
    if user_data:
        email, is_active, is_approved = user_data
        print(f"📧 Test user: {email}")
        print(f"🔆 Active: {'Yes' if is_active else 'No'}")
        print(f"✅ Approved: {'Yes' if is_approved else 'No'}")
    else:
        print("❌ Test user not found")
        conn.close()
        return
    
    conn.close()
    
    # Test login attempt
    print("\n🧪 Attempting login with inactive user...")
    
    try:
        session = requests.Session()
        
        # Get login page first (might need CSRF token)
        login_page_response = session.get('http://127.0.0.1:8080/auth/login')
        
        if login_page_response.status_code != 200:
            print(f"❌ Cannot access login page: {login_page_response.status_code}")
            return
        
        # Attempt login
        login_data = {
            'email': 'inactive.test@example.com',
            'password': 'testpassword123'
        }
        
        login_response = session.post('http://127.0.0.1:8080/auth/login', data=login_data, allow_redirects=False)
        
        print(f"📊 Login response status: {login_response.status_code}")
        
        # Check if we were redirected (successful login would redirect to dashboard)
        if login_response.status_code == 302:
            location = login_response.headers.get('Location', '')
            if 'login' in location:
                print("✅ Login blocked - redirected back to login page")
            else:
                print("❌ Login may have succeeded - unexpected redirect")
                print(f"   Redirect location: {location}")
        else:
            # Check response content for error messages
            content = login_response.text.lower()
            if 'deactivated' in content or 'inactive' in content:
                print("✅ Login blocked - inactive account message shown")
            elif 'error' in content:
                print("✅ Login blocked - error message shown")
            else:
                print("❓ Login response unclear - manual verification needed")
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server")
        print("   Make sure server is running at http://127.0.0.1:8080")
    
    except Exception as e:
        print(f"❌ Error during login test: {e}")

if __name__ == "__main__":
    test_inactive_user_login()
    
    print("\n" + "=" * 50)
    print("🎯 Manual Testing Steps:")
    print("1. Go to http://127.0.0.1:8080/auth/login")
    print("2. Try to login with:")
    print("   Email: inactive.test@example.com")
    print("   Password: testpassword123")
    print("3. Should see error: 'Your account has been deactivated'")
    print("4. Login should be blocked")
    print("=" * 50)
