#!/usr/bin/env python3
"""
Debug script to test if the account-info route is properly registered
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def debug_routes():
    """Debug all registered routes"""
    
    app = create_app()
    
    with app.app_context():
        print("=== FLASK ROUTES DEBUG ===")
        print()
        
        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods or []),
                'rule': rule.rule
            })
        
        # Filter SMS-related routes
        sms_routes = [r for r in routes if 'sms' in r['rule'].lower()]
        
        print("📋 SMS-RELATED ROUTES:")
        print("-" * 80)
        for route in sorted(sms_routes, key=lambda x: x['rule']):
            methods = [m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']]
            print(f"  {route['rule']:<50} | {', '.join(methods):<15} | {route['endpoint']}")
        
        print()
        
        # Check specifically for account-info route
        account_routes = [r for r in routes if 'account' in r['rule'].lower()]
        
        print("🔍 ACCOUNT-INFO RELATED ROUTES:")
        print("-" * 80)
        if account_routes:
            for route in account_routes:
                methods = [m for m in route['methods'] if m not in ['HEAD', 'OPTIONS']]
                print(f"✅ {route['rule']:<50} | {', '.join(methods):<15} | {route['endpoint']}")
        else:
            print("❌ No account-info routes found!")
        
        print()
        
        # Test if the expected route exists
        expected_routes = [
            '/sms-settings/sms-settings/account-info',
            '/sms-settings/account-info'
        ]
        
        print("🎯 EXPECTED ROUTE CHECK:")
        print("-" * 80)
        all_rules = [rule.rule for rule in app.url_map.iter_rules()]
        
        for expected in expected_routes:
            if expected in all_rules:
                print(f"✅ {expected} - FOUND")
            else:
                print(f"❌ {expected} - NOT FOUND")
        
        print()
        print("✅ DEBUG COMPLETED!")

if __name__ == '__main__':
    debug_routes()
