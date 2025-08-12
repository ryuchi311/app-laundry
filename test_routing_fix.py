#!/usr/bin/env python3
"""
Simple test to verify routing fix works.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

def test_routing_fix():
    """Test the routing fix"""
    app = create_app()
    
    with app.test_request_context('/'):
        from flask import url_for
        
        print("🧪 Testing Routing Fix")
        print("=" * 25)
        
        try:
            # Test the routes we fixed
            service_url = url_for('service.list_services')
            print(f"✅ service.list_services: {service_url}")
            
            expenses_list_url = url_for('expenses.list_expenses')  
            print(f"✅ expenses.list_expenses: {expenses_list_url}")
            
            expenses_add_url = url_for('expenses.add_expense')
            print(f"✅ expenses.add_expense: {expenses_add_url}")
            
            dashboard_url = url_for('views.dashboard')
            print(f"✅ views.dashboard: {dashboard_url}")
            
            customize_url = url_for('views.customize_dashboard')
            print(f"✅ views.customize_dashboard: {customize_url}")
            
            print("\n🎉 All routes are working correctly!")
            return True
            
        except Exception as e:
            print(f"❌ Route test failed: {str(e)}")
            return False

def main():
    success = test_routing_fix()
    if success:
        print("\n✅ Dashboard routing issues have been resolved!")
    else:
        print("\n❌ Some routing issues remain.")

if __name__ == "__main__":
    main()
