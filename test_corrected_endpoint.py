#!/usr/bin/env python3
"""
Test the corrected account information endpoint
"""

import requests
import json

def test_corrected_endpoint():
    """Test the correct account info endpoint URL"""
    
    base_url = "http://127.0.0.1:5000"
    correct_endpoint = "/sms-settings/sms-settings/account-info"
    full_url = f"{base_url}{correct_endpoint}"
    
    print("=== CORRECTED ENDPOINT TEST ===")
    print(f"Testing: {full_url}")
    
    try:
        response = requests.get(full_url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if response.status_code == 200:
            # Check if this is the login page or actual JSON
            if "Sign in to your account" in response.text:
                print("❌ Getting login page - authentication required")
                print("✅ Endpoint exists but requires authentication")
                return "auth_required"
            elif "application/json" in response.headers.get('Content-Type', ''):
                try:
                    data = response.json()
                    print("✅ JSON Response received!")
                    print(f"Data: {json.dumps(data, indent=2)}")
                    return "success"
                except:
                    print("❌ Response claims to be JSON but isn't valid")
            else:
                print("❌ Getting unexpected content type")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return "error"
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is Flask app running?")
        return "connection_error"
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return "error"
    
    return "unknown"

def simulate_browser_session():
    """Simulate what happens when user clicks refresh in browser"""
    
    print("\n=== BROWSER SESSION SIMULATION ===")
    print("This simulates what happens when:")
    print("1. User logs into the app via browser")
    print("2. User navigates to Bulk SMS Marketing page") 
    print("3. User clicks 'Refresh' button")
    print()
    
    session = requests.Session()
    base_url = "http://127.0.0.1:5000"
    
    # Step 1: Get login page (to simulate browser session start)
    print("Step 1: Getting login page...")
    login_page = session.get(f"{base_url}/auth/login")
    print(f"Login page status: {login_page.status_code}")
    
    # Step 2: Try to access bulk message page (will redirect to login)
    print("\nStep 2: Accessing bulk message page...")
    bulk_page = session.get(f"{base_url}/sms-settings/sms-settings/bulk-message")
    print(f"Bulk page status: {bulk_page.status_code}")
    
    if "Sign in to your account" in bulk_page.text:
        print("✅ Correctly redirected to login (as expected)")
        
        # Step 3: Now try account info endpoint (should also redirect)
        print("\nStep 3: Testing account info endpoint with same session...")
        account_response = session.get(f"{base_url}/sms-settings/sms-settings/account-info")
        print(f"Account info status: {account_response.status_code}")
        
        if "Sign in to your account" in account_response.text:
            print("✅ Account endpoint correctly requires authentication")
            print("✅ The fix (adding credentials: 'same-origin') should work!")
        else:
            print("❌ Unexpected response from account endpoint")
    else:
        print("❌ Not getting expected login redirect")

if __name__ == "__main__":
    # Test the corrected endpoint URL
    result = test_corrected_endpoint()
    
    # Simulate browser session behavior
    simulate_browser_session()
    
    print(f"\n=== SUMMARY ===")
    if result == "auth_required":
        print("✅ DIAGNOSIS: Account info endpoint is working correctly!")
        print("✅ ISSUE: Authentication required (this is expected)")
        print("✅ FIX APPLIED: Added 'credentials: same-origin' to fetch request")
        print("✅ NEXT STEP: Test in browser with logged-in user")
    elif result == "success":
        print("✅ Endpoint working without auth (unexpected but good)")
    else:
        print("❌ There may be other issues to investigate")
        
    print("\n📋 TO TEST THE FIX:")
    print("1. Open browser: http://127.0.0.1:5000")
    print("2. Log in to your laundry app") 
    print("3. Go to: SMS Settings → Bulk SMS Marketing")
    print("4. Click 'Refresh' button in Account Information section")
    print("5. Should now work without errors!")
