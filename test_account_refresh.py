#!/usr/bin/env python3
"""
Test script to diagnose account information refresh errors
"""

import requests
import json
from requests.auth import HTTPBasicAuth

def test_account_info_endpoint():
    """Test the account information refresh endpoint"""
    
    base_url = "http://127.0.0.1:5000"
    endpoint = "/sms-settings/sms-settings/account-info"
    full_url = f"{base_url}{endpoint}"
    
    print("=== ACCOUNT INFO ENDPOINT TEST ===")
    print(f"Testing endpoint: {full_url}")
    
    try:
        # Test without authentication first
        print("\n1. Testing without authentication...")
        response = requests.get(full_url, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("✅ Authentication required (expected)")
        elif response.status_code == 200:
            print("✅ Request successful")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("Make sure Flask app is running on http://127.0.0.1:5000")
        return False
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    # Test with basic authentication (if needed)
    print("\n2. Testing with basic authentication...")
    try:
        # Common default credentials for testing
        auth = HTTPBasicAuth('admin', 'admin')
        response = requests.get(full_url, auth=auth, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Authentication successful")
            try:
                data = response.json()
                print(f"Response data: {json.dumps(data, indent=2)}")
            except:
                print(f"Response text: {response.text}")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Auth test error: {e}")
    
    print("\n=== TEST COMPLETE ===")
    return True

def test_bulk_message_page():
    """Test if the bulk message page loads correctly"""
    
    base_url = "http://127.0.0.1:5000"
    endpoint = "/sms-settings/sms-settings/bulk-message"
    full_url = f"{base_url}{endpoint}"
    
    print("\n=== BULK MESSAGE PAGE TEST ===")
    print(f"Testing page: {full_url}")
    
    try:
        response = requests.get(full_url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Page loads successfully")
            # Check if account info section exists
            if "Account Information" in response.text:
                print("✅ Account Information section found")
            else:
                print("❌ Account Information section not found")
        else:
            print(f"❌ Page load failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Page test error: {e}")

if __name__ == "__main__":
    print("Starting account information refresh diagnostic...")
    test_account_info_endpoint()
    test_bulk_message_page()
