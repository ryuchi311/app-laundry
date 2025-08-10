#!/usr/bin/env python3
"""
Test account information refresh with proper authentication
"""

import requests
import json
from requests import Session

def test_account_refresh_with_login():
    """Test the account refresh functionality with proper login simulation"""
    
    base_url = "http://127.0.0.1:5000"
    session = Session()
    
    print("=== ACCOUNT REFRESH WITH LOGIN TEST ===")
    
    # Step 1: Try to access the bulk message page (should redirect to login)
    print("\n1. Testing bulk message page access...")
    bulk_url = f"{base_url}/sms-settings/sms-settings/bulk-message"
    
    try:
        response = session.get(bulk_url)
        print(f"Status Code: {response.status_code}")
        
        if "Sign in to your account" in response.text:
            print("✅ Correctly redirected to login page")
            
            # Step 2: Simulate login (we'll need to check what login endpoint exists)
            print("\n2. Simulating login...")
            login_url = f"{base_url}/auth/login"
            
            # Try to get the login form first to extract any CSRF tokens
            login_page = session.get(login_url)
            if login_page.status_code == 200:
                print("✅ Login page accessible")
                
                # Try a simple POST login (adapt credentials as needed)
                login_data = {
                    'email': 'admin@example.com',  # Common test credentials
                    'password': 'admin'
                }
                
                login_response = session.post(login_url, data=login_data, allow_redirects=False)
                print(f"Login attempt status: {login_response.status_code}")
                
                if login_response.status_code in [302, 303]:  # Redirect after successful login
                    print("✅ Login appears successful (got redirect)")
                    
                    # Step 3: Try bulk message page again
                    print("\n3. Testing bulk message page after login...")
                    bulk_response = session.get(bulk_url)
                    
                    if bulk_response.status_code == 200 and "Create Bulk Message" in bulk_response.text:
                        print("✅ Bulk message page now accessible")
                        
                        # Step 4: Test account info endpoint
                        print("\n4. Testing account info endpoint...")
                        account_url = f"{base_url}/sms-settings/account-info"
                        
                        account_response = session.get(account_url)
                        print(f"Account info status: {account_response.status_code}")
                        
                        if account_response.status_code == 200:
                            try:
                                account_data = account_response.json()
                                print("✅ Account info endpoint working!")
                                print(f"Response: {json.dumps(account_data, indent=2)}")
                                
                                return True
                            except:
                                print(f"Account info response (text): {account_response.text[:200]}...")
                        else:
                            print(f"❌ Account info failed: {account_response.status_code}")
                            print(f"Response: {account_response.text[:200]}...")
                    else:
                        print(f"❌ Bulk message page still not accessible: {bulk_response.status_code}")
                else:
                    print(f"❌ Login failed: {login_response.status_code}")
                    print(f"Response: {login_response.text[:200]}...")
            else:
                print(f"❌ Login page not accessible: {login_page.status_code}")
        else:
            print("❌ Expected login redirect but got different response")
            print(f"Response snippet: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False
    
    return False

def test_direct_account_endpoint():
    """Test the account endpoint directly with session handling"""
    
    print("\n=== DIRECT ACCOUNT ENDPOINT TEST ===")
    
    session = Session()
    base_url = "http://127.0.0.1:5000"
    
    # Test if there's a way to authenticate directly or if we need special headers
    account_url = f"{base_url}/sms-settings/account-info"
    
    print(f"Testing: {account_url}")
    
    try:
        response = session.get(account_url)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            if "application/json" in response.headers.get('Content-Type', ''):
                try:
                    data = response.json()
                    print("✅ JSON Response received!")
                    print(f"Data: {json.dumps(data, indent=2)}")
                    return True
                except:
                    print("❌ Response is not valid JSON")
            else:
                print("❌ Response is not JSON (likely HTML login page)")
                if "Sign in to your account" in response.text:
                    print("❌ Confirmed: Redirected to login page")
        else:
            print(f"❌ Non-200 status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    print("Testing account information refresh functionality...")
    
    # Test direct endpoint first
    direct_success = test_direct_account_endpoint()
    
    # Test with simulated login
    login_success = test_account_refresh_with_login()
    
    if direct_success or login_success:
        print("\n✅ TEST RESULT: Account refresh functionality working!")
    else:
        print("\n❌ TEST RESULT: Account refresh needs authentication fix")
        
    print("\nTo test properly, please:")
    print("1. Open browser to http://127.0.0.1:5000")
    print("2. Log in to the application")
    print("3. Navigate to SMS Settings > Bulk SMS Marketing")
    print("4. Click the 'Refresh' button in the Account Information section")
