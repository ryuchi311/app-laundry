#!/usr/bin/env python3
"""
Test script to validate all routes used in the dashboard template.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from flask import url_for

def test_dashboard_routes():
    """Test all routes referenced in the dashboard template"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing All Dashboard Routes")
        print("=" * 40)
        
        # Routes used in dashboard template
        routes_to_test = [
            # Main navigation routes
            ('customer.list_customers', 'Customer List'),
            ('laundry.list_laundries', 'Laundry List'),
            ('laundry.add_laundry', 'Add Laundry'),
            ('service.list_services', 'Service List'),
            ('inventory.list_items', 'Inventory List'),
            ('inventory.add_item', 'Add Inventory Item'),
            ('expenses.list_expenses', 'Expenses List'),
            ('expenses.add_expense', 'Add Expense'),
            ('customer.add_customer', 'Add Customer'),
            
            # Dashboard customization routes
            ('views.customize_dashboard', 'Customize Dashboard'),
            ('views.dashboard', 'Main Dashboard'),
        ]
        
        failed_routes = []
        passed_routes = []
        
        for endpoint, description in routes_to_test:
            try:
                url = url_for(endpoint)
                passed_routes.append((endpoint, description, url))
                print(f"✅ {description}: {endpoint} → {url}")
            except Exception as e:
                failed_routes.append((endpoint, description, str(e)))
                print(f"❌ {description}: {endpoint} → ERROR: {str(e)}")
        
        print(f"\n📊 Results:")
        print(f"✅ Passed: {len(passed_routes)}")
        print(f"❌ Failed: {len(failed_routes)}")
        
        if failed_routes:
            print(f"\n🔧 Routes to Fix:")
            for endpoint, description, error in failed_routes:
                print(f"   • {endpoint} ({description}): {error}")
            return False
        else:
            print(f"\n🎉 All dashboard routes are valid!")
            return True

def test_dashboard_rendering():
    """Test that dashboard template renders without errors"""
    app = create_app()
    
    print(f"\n🎨 Testing Dashboard Template Rendering")
    print("=" * 45)
    
    try:
        with app.test_client() as client:
            # Test GET request to dashboard (will redirect to login, but template should be loadable)
            response = client.get('/', follow_redirects=False)
            
            if response.status_code in [200, 302]:  # 200 = success, 302 = redirect to login
                print(f"✅ Dashboard route returns status {response.status_code}")
                
                # Try to render with a test request context
                with app.test_request_context():
                    try:
                        template = app.jinja_env.get_template('dashboard.html')
                        print("✅ Dashboard template loads successfully")
                        
                        # Test template variable handling
                        test_context = {
                            'user_widgets': [],
                            'total_customers': 0,
                            'active_laundries': 0,
                            'completed_laundries': 0,
                            'total_revenue': 0,
                            'estimated_revenue': 0,
                            'total_services': 0,
                            'active_services': 0,
                            'popular_services': [],
                            'all_services': [],
                            'recent_laundries': [],
                            'recent_expenses': [],
                            'total_inventory_items': 0,
                            'low_stock_items': [],
                            'out_of_stock_items': [],
                            'total_inventory_value': 0
                        }
                        
                        # This would fail if there are template syntax or routing errors
                        rendered = template.render(**test_context)
                        print("✅ Dashboard template renders with test data")
                        
                        return True
                    except Exception as e:
                        print(f"❌ Template rendering failed: {str(e)}")
                        return False
            else:
                print(f"❌ Dashboard route returned unexpected status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Dashboard rendering test failed: {str(e)}")
        return False

def main():
    print("🚀 Dashboard Route Validation Test")
    print("=" * 50)
    
    success = True
    success &= test_dashboard_routes()
    success &= test_dashboard_rendering()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\n✅ Summary:")
        print("   • All dashboard routes are valid")
        print("   • Template renders without errors")
        print("   • Dashboard is ready for use")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the errors above and fix any issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
