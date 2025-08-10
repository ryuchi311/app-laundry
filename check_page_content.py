#!/usr/bin/env python3
"""
Simple test to see what content we're getting from the bulk message page
"""

import requests

def check_page_content():
    """Check what content we're actually getting"""
    
    base_url = "http://127.0.0.1:5000"
    bulk_url = f"{base_url}/sms-settings/sms-settings/bulk-message"
    
    print("=== PAGE CONTENT CHECK ===")
    
    try:
        response = requests.get(bulk_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # Show first 500 characters of the response
        print(f"\nFirst 500 characters of response:")
        print("-" * 50)
        print(response.text[:500])
        print("-" * 50)
        
        # Check for key indicators
        if "Sign in to your account" in response.text:
            print("\n✅ Getting login page (authentication required)")
        elif "Create Bulk Message" in response.text:
            print("\n✅ Getting bulk message page")
        elif "Account Information" in response.text:
            print("\n❌ Account Information still present!")
        else:
            print("\n❓ Getting unknown page content")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_page_content()
