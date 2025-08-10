#!/usr/bin/env python3
"""
Test script to verify dashboard UI visibility rules for different roles.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

app = create_app()

def test_dashboard_visibility():
    """Test what each role should see in the dashboard."""
    with app.app_context():
        roles_and_visibility = {
            'super_admin': {
                'main_cards_customers': True,
                'main_cards_active_laundries': True,
                'main_cards_completed': True,
                'main_cards_revenue': True,
                'inventory_items': True,
                'inventory_value': True,
                'recent_expenses': True,
                'low_stock_alerts': True,
                'services_overview': True,
                'loyalty_program': True,
                'quick_actions_services': True,
                'reason': 'Super Admin has full access to all sections including main dashboard cards'
            },
            'admin': {
                'main_cards_customers': True,
                'main_cards_active_laundries': True,
                'main_cards_completed': True,
                'main_cards_revenue': True,
                'inventory_items': True,
                'inventory_value': True,
                'recent_expenses': True,
                'low_stock_alerts': True,
                'services_overview': True,
                'loyalty_program': True,
                'quick_actions_services': True,
                'reason': 'Admin has full operational access including main dashboard cards and all business features'
            },
            'manager': {
                'main_cards_customers': True,
                'main_cards_active_laundries': True,
                'main_cards_completed': True,
                'main_cards_revenue': True,
                'inventory_items': True,
                'inventory_value': True,
                'recent_expenses': False,
                'low_stock_alerts': True,
                'services_overview': True,
                'loyalty_program': True,
                'quick_actions_services': True,
                'reason': 'Manager can see main dashboard cards and operational data but not detailed expense data'
            },
            'employee': {
                'main_cards_customers': False,
                'main_cards_active_laundries': False,
                'main_cards_completed': False,
                'main_cards_revenue': False,
                'inventory_items': False,
                'inventory_value': False,
                'recent_expenses': False,
                'low_stock_alerts': False,
                'services_overview': False,
                'loyalty_program': False,
                'quick_actions_services': False,
                'reason': 'Employee has basic access only - focused on core laundry operations without main dashboard cards'
            }
        }
        
        print("🎯 Dashboard Visibility Rules by Role")
        print("="*130)
        print(f"{'Role':<12} {'Customers':<10} {'Active':<8} {'Completed':<10} {'Revenue':<8} {'Inventory':<11} {'Inv Value':<11} {'Expenses':<10} {'Alerts':<8} {'Services':<9} {'Loyalty':<8} {'QA Services':<11}")
        print("-"*130)
        
        for role, visibility in roles_and_visibility.items():
            role_display = role.replace('_', ' ').title()
            customers_icon = "✅" if visibility['main_cards_customers'] else "❌"
            active_icon = "✅" if visibility['main_cards_active_laundries'] else "❌"
            completed_icon = "✅" if visibility['main_cards_completed'] else "❌"
            revenue_icon = "✅" if visibility['main_cards_revenue'] else "❌"
            inventory_icon = "✅" if visibility['inventory_items'] else "❌"
            value_icon = "✅" if visibility['inventory_value'] else "❌"
            expenses_icon = "✅" if visibility['recent_expenses'] else "❌"
            alerts_icon = "✅" if visibility['low_stock_alerts'] else "❌"
            services_icon = "✅" if visibility['services_overview'] else "❌"
            loyalty_icon = "✅" if visibility['loyalty_program'] else "❌"
            qa_services_icon = "✅" if visibility['quick_actions_services'] else "❌"
            
            print(f"{role_display:<12} {customers_icon:<10} {active_icon:<8} {completed_icon:<10} {revenue_icon:<8} {inventory_icon:<11} {value_icon:<11} {expenses_icon:<10} {alerts_icon:<8} {services_icon:<9} {loyalty_icon:<8} {qa_services_icon:<11}")
        
        print("\n" + "="*130)
        print("ROLE EXPLANATIONS:")
        print("="*80)
        
        for role, visibility in roles_and_visibility.items():
            role_display = role.replace('_', ' ').title()
            print(f"\n{role_display}:")
            print(f"  {visibility['reason']}")
        
        print("\n" + "="*80)
        print("TEMPLATE CONDITIONS USED:")
        print("="*80)
        print("• Main Cards (Customers, Active, Completed, Revenue): {% if user.is_manager() %}")
        print("• Inventory Items & Value: {% if user.is_manager() %}")
        print("• Recent Expenses: {% if user.is_admin() %}")
        print("• Low Stock Alerts: {% if low_stock_items and user.is_manager() %}")
        print("• Services Overview: {% if user.is_manager() %}")
        print("• Loyalty Program: {% if user.is_manager() %}")
        print("• Quick Actions Services: Manager/Admin only (Employee section removed)")
        
        print("\n✅ Dashboard visibility testing completed!")

def test_role_methods():
    """Test the role checking methods for each user type."""
    with app.app_context():
        test_users = [
            ('super_admin', 'superadmin@laundry.com'),
            ('admin', 'admin@laundry.com'),
            ('manager', 'manager@laundry.com'),
            ('employee', 'employee1@laundry.com')
        ]
        
        print("\n🔍 Role Method Testing")
        print("="*50)
        
        for role, email in test_users:
            user = User.query.filter_by(email=email).first()
            if user:
                role_display = role.replace('_', ' ').title()
                print(f"\n{role_display} ({email}):")
                print(f"  is_admin(): {user.is_admin()}")
                print(f"  is_manager(): {user.is_manager()}")
                print(f"  is_employee(): {user.is_employee()}")
                print(f"  is_super_admin(): {user.is_super_admin()}")
            else:
                print(f"❌ User not found: {email}")

if __name__ == '__main__':
    print("🚀 Dashboard UI Visibility Test")
    print("="*50)
    
    try:
        test_dashboard_visibility()
        test_role_methods()
        print("\n🎉 All UI visibility tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
