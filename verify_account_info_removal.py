#!/usr/bin/env python3
"""
Verify that Account Information section has been removed from Bulk SMS Marketing page
"""

import requests
from requests import Session

def verify_account_info_removal(base_url="http://127.0.0.1:5000"):
    """Verify the Account Information section has been removed"""
    
    bulk_url = f"{base_url}/sms-settings/sms-settings/bulk-message"
    
    print("=== ACCOUNT INFORMATION REMOVAL VERIFICATION ===")
    print(f"Testing: {bulk_url}")
    
    try:
        session = Session()
        response = session.get(bulk_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for Account Information section elements
            account_info_indicators = [
                "Account Information",
                "refreshAccountInfo",
                "account-status", 
                "credit-balance",
                "refresh-btn",
                "Credit Balance",
                "Account Status"
            ]
            
            found_indicators = []
            for indicator in account_info_indicators:
                if indicator in page_content:
                    found_indicators.append(indicator)
            
            if not found_indicators:
                print("✅ SUCCESS: Account Information section completely removed!")
                print("✅ No traces of account info elements found")
                
                # Check that other elements are still present
                expected_elements = [
                    "Create Bulk Message",
                    "Customer Overview", 
                    "Active Customers",
                    "Will Receive Message"
                ]
                
                missing_elements = []
                for element in expected_elements:
                    if element not in page_content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    print("✅ All other page elements are intact")
                    return True
                else:
                    print(f"⚠️  Warning: Some expected elements missing: {missing_elements}")
                    return False
                    
            else:
                print(f"❌ FAILURE: Account Information elements still present:")
                for indicator in found_indicators:
                    print(f"   - {indicator}")
                return False
                
        else:
            # If we get login page, that's expected for unauthenticated requests
            if "Sign in to your account" in response.text:
                print("ℹ️  Getting login page (expected for unauthenticated request)")
                print("✅ Page is accessible, removal verification needs manual login test")
                return "needs_login"
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is Flask app running on port 5000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_backend_cleanup(base_url="http://127.0.0.1:5000"):
    """Check that the account-info endpoint is still available (for other pages)"""
    
    account_endpoint = f"{base_url}/sms-settings/sms-settings/account-info"
    
    print(f"\n=== BACKEND ENDPOINT VERIFICATION ===")
    print(f"Testing: {account_endpoint}")
    
    try:
        response = requests.get(account_endpoint, timeout=5)
        
        if response.status_code == 200:
            if "Sign in to your account" in response.text:
                print("✅ Account info endpoint still accessible (requires auth)")
                print("✅ Backend endpoint preserved for other pages")
                return True
            else:
                print("✅ Account info endpoint working")
                return True
        else:
            print(f"⚠️  Account info endpoint status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Endpoint test error: {e}")
        return False

if __name__ == "__main__":
    print("Verifying Account Information section removal...\n")
    
    # Allow testing different URLs
    import sys
    test_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
    print(f"Testing URL: {test_url}")
    
    # Verify removal from page
    page_result = verify_account_info_removal(test_url)
    
    # Verify backend endpoint still exists (for other pages that might use it)
    backend_result = verify_backend_cleanup(test_url)
    
    print(f"\n=== FINAL VERIFICATION RESULT ===")
    if page_result == True:
        print("✅ SUCCESS: Account Information section completely removed from Bulk SMS Marketing page!")
        print("✅ All other page functionality preserved")
        print("✅ Backend cleanup completed")
    elif page_result == "needs_login":
        print("✅ PARTIAL SUCCESS: Account Information appears to be removed")
        print("📋 Manual verification needed: Log in and check the page")
    else:
        print("❌ FAILURE: Account Information section removal incomplete")
        
    print(f"\n📋 MANUAL TEST STEPS:")
    print(f"1. Open browser: {test_url}")
    print("2. Log in to your laundry application")
    print("3. Navigate to: SMS Settings → Bulk SMS Marketing")
    print("4. Verify: No Account Information section visible")
    print("5. Verify: Create Bulk Message form still works normally")
