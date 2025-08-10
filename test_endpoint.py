#!/usr/bin/env python3
"""
Quick test script to verify the account-info endpoint is working
"""

import requests
import json

def test_account_info_endpoint():
    """Test the /sms-settings/account-info endpoint"""
    
    print("=== ACCOUNT INFO ENDPOINT TEST ===")
    print()
    
    # Test the corrected endpoint URL
    url = "http://127.0.0.1:5000/sms-settings/sms-settings/account-info"
    
    try:
        print(f"🔍 Testing endpoint: {url}")
        
        # Make request with session to handle login if needed
        session = requests.Session()
        
        response = session.get(url)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Endpoint is working!")
            try:
                data = response.json()
                print(f"📝 Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"📝 Response Text: {response.text}")
        
        elif response.status_code == 404:
            print("❌ ERROR: Endpoint not found (404)")
            print("   This means the route is not properly registered")
            
        elif response.status_code == 302:
            print("🔄 REDIRECT: Authentication required")
            print(f"   Redirect Location: {response.headers.get('Location', 'Unknown')}")
            
        else:
            print(f"⚠️  UNEXPECTED: Status code {response.status_code}")
            print(f"   Response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR: Flask app is not running")
        print("   Please make sure the Flask app is running on http://127.0.0.1:5000")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    print()
    print("✅ TEST COMPLETED!")

if __name__ == '__main__':
    test_account_info_endpoint()
