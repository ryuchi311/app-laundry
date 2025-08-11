#!/usr/bin/env python3
"""
Test script to verify the charts page fix
"""

import requests

def test_charts_page():
    """Test that the charts page loads without errors"""
    
    print("🧪 Testing Charts Page Fix")
    print("=" * 40)
    
    try:
        # Test the charts page
        response = requests.get('http://127.0.0.1:8080/charts')
        
        print(f"📊 Charts page response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Charts page loaded successfully!")
            
            # Check if the page contains expected content
            content = response.text.lower()
            
            if 'chart' in content:
                print("✅ Page contains chart content")
            
            if 'inventory' in content:
                print("✅ Page contains inventory information")
            
            if 'revenue' in content:
                print("✅ Page contains revenue information")
            
            print(f"📄 Page size: {len(response.text)} characters")
            
        elif response.status_code == 302:
            print("🔄 Redirected (probably need to login first)")
            print("   Try logging in at http://127.0.0.1:8080/auth/login")
        
        else:
            print(f"❌ Page returned status code: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask server")
        print("   Make sure server is running at http://127.0.0.1:8080")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_charts_page()
    
    print("\n" + "=" * 40)
    print("🎯 If the page loads successfully:")
    print("1. The charts page should now display without errors")
    print("2. Inventory value should show ₱0.00 (if no inventory items)")
    print("3. Stock alerts should show 0 items low/out of stock")
    print("4. All dashboard metrics should be displayed correctly")
