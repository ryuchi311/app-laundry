#!/usr/bin/env python3
"""
Test the inventory check API endpoint
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

def test_api_endpoint():
    app = create_app()
    
    print("🧪 Testing API Endpoint Registration:")
    print("=" * 50)
    
    with app.app_context():
        # List all routes
        routes = []
        for rule in app.url_map.iter_rules():
            if 'inventory' in rule.rule or 'check' in rule.rule or 'api' in rule.rule:
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods) if rule.methods else [],
                    'rule': rule.rule
                })
        
        print("📍 API Routes Found:")
        for route in routes:
            print(f"   ✅ {route['rule']} [{', '.join(route['methods'])}] -> {route['endpoint']}")
        
        # Check specifically for our endpoint
        inventory_check_found = False
        for rule in app.url_map.iter_rules():
            if 'check-inventory' in rule.rule:
                inventory_check_found = True
                print(f"\n🎯 Found Inventory Check Endpoint:")
                print(f"   ✅ URL: {rule.rule}")
                print(f"   ✅ Methods: {list(rule.methods) if rule.methods else []}")
                print(f"   ✅ Endpoint: {rule.endpoint}")
                break
        
        if not inventory_check_found:
            print("\n❌ Inventory check endpoint not found!")
            print("Available endpoints:")
            for rule in app.url_map.iter_rules():
                print(f"   - {rule.rule}")
        
        return inventory_check_found

if __name__ == "__main__":
    success = test_api_endpoint()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}: API endpoint test")
