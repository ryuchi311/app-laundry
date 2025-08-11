#!/usr/bin/env python3
"""
Quick test to verify the template fix
"""

import requests

def test_user_management_page():
    """Test that the user management page loads without errors"""
    
    try:
        # Test the user management page
        response = requests.get('http://127.0.0.1:8080/user-management/users')
        
        if response.status_code == 200:
            print("✅ User Management page loaded successfully!")
            
            # Check if the page contains expected content
            content = response.text.lower()
            
            if 'user management' in content:
                print("✅ Page contains user management header")
            
            if 'pending' in content:
                print("✅ Page shows pending users information")
            
            if 'system users' in content:
                print("✅ Page shows system users section")
            
            print(f"📄 Page size: {len(response.text)} characters")
            
        elif response.status_code == 302:
            print("🔄 Redirected (probably need to login first)")
            print("   Try logging in at http://127.0.0.1:8080/auth/login")
        
        else:
            print(f"❌ Page returned status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server")
        print("   Make sure the server is running at http://127.0.0.1:8080")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🧪 Testing User Management Page Fix")
    print("=" * 40)
    test_user_management_page()
    print("=" * 40)
    print("🎯 If you see a redirect, log in first:")
    print("   Email: ryuchicago@gmail.com (or other super admin)")
    print("   Then visit: http://127.0.0.1:8080/user-management/users")
