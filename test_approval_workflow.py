#!/usr/bin/env python3
"""
Test script to demonstrate the user approval workflow
"""

import sys
import os
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_user_approval_workflow():
    """Test the complete user approval workflow"""
    base_url = "http://127.0.0.1:5000"
    
    print("🧪 Testing User Approval Workflow")
    print("=" * 50)
    
    # Test 1: Try to register a new user
    print("\n1. Testing user registration...")
    
    # Create a session for making requests
    session = requests.Session()
    
    # First get the signup page to get CSRF token (if needed)
    try:
        signup_response = session.get(f"{base_url}/signup")
        if signup_response.status_code == 200:
            print("✅ Signup page accessible")
            
            # Try to register a new user
            signup_data = {
                'email': 'testuser@laundry.com',
                'password': 'testpassword',
                'confirm_password': 'testpassword',
                'full_name': 'Test User',
                'phone': '09987654321'
            }
            
            register_response = session.post(f"{base_url}/signup", data=signup_data)
            if register_response.status_code == 200 or register_response.status_code == 302:
                print("✅ New user registration submitted")
            else:
                print(f"❌ Registration failed: {register_response.status_code}")
        else:
            print(f"❌ Cannot access signup page: {signup_response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server. Make sure it's running on http://127.0.0.1:5000")
        return
    
    # Test 2: Try to login with the new user (should fail)
    print("\n2. Testing login with unapproved user...")
    
    try:
        login_data = {
            'email': 'testuser@laundry.com',
            'password': 'testpassword'
        }
        
        login_response = session.post(f"{base_url}/login", data=login_data)
        if "approval" in login_response.text.lower() or "pending" in login_response.text.lower():
            print("✅ Unapproved user correctly blocked from login")
        else:
            print("❓ User login response unclear - check manually")
            
    except Exception as e:
        print(f"❌ Error testing login: {e}")
    
    # Test 3: Login as super admin
    print("\n3. Testing super admin login...")
    
    try:
        admin_session = requests.Session()
        admin_login_data = {
            'email': 'admin@laundry.com',
            'password': 'admin123'
        }
        
        admin_login_response = admin_session.post(f"{base_url}/login", data=admin_login_data)
        if admin_login_response.status_code == 200 or admin_login_response.status_code == 302:
            print("✅ Super admin login successful")
            
            # Try to access user management
            user_management_response = admin_session.get(f"{base_url}/user-management/")
            if user_management_response.status_code == 200:
                print("✅ Super admin can access user management")
                
                if "pending" in user_management_response.text.lower():
                    print("✅ Pending users visible in user management")
                else:
                    print("❓ Pending users status unclear - check manually")
            else:
                print(f"❌ Cannot access user management: {user_management_response.status_code}")
        else:
            print(f"❌ Super admin login failed: {admin_login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing admin login: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Manual Testing Instructions:")
    print("1. Open http://127.0.0.1:5000/signup in your browser")
    print("2. Register a new user with email: newuser@test.com")
    print("3. Try to login with that user - should be blocked")
    print("4. Login as admin@laundry.com / admin123")
    print("5. Go to User Management - should see pending user")
    print("6. Approve the user using the Approve button")
    print("7. New user should now be able to login")
    print("=" * 50)

if __name__ == '__main__':
    test_user_approval_workflow()
