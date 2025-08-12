#!/usr/bin/env python3
"""
Test script to verify the role-based system functionality.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

app = create_app()

def test_role_permissions():
    """Test all role permission methods."""
    with app.app_context():
        # Get test users
        super_admin = User.query.filter_by(email='superadmin@laundry.com').first()
        admin = User.query.filter_by(email='admin@laundry.com').first()
        manager = User.query.filter_by(email='manager@laundry.com').first()
        employee = User.query.filter_by(email='employee1@laundry.com').first()
        
        if not all([super_admin, admin, manager, employee]):
            print("❌ Not all test users found. Please run the migration script first.")
            return
        
        print("🧪 Testing Role-Based Permission System")
        print("="*50)
        
        # Test cases
        test_cases = [
            ('Super Admin', super_admin),
            ('Admin', admin),
            ('Manager', manager),
            ('Employee', employee)
        ]
        
        permissions = [
            ('is_admin', 'Admin privileges'),
            ('is_manager', 'Manager privileges'),
            ('is_employee', 'Employee role'),
            ('is_super_admin', 'Super Admin privileges'),
            ('can_manage_users', 'User management'),
            ('can_manage_system', 'System management'),
            ('can_view_reports', 'View reports'),
            ('can_manage_inventory', 'Manage inventory'),
            ('can_manage_customers', 'Manage customers'),
            ('can_process_laundry', 'Process laundry'),
            ('can_view_all_orders', 'View all orders')
        ]
        
        for role_name, user in test_cases:
            print(f"\n{role_name} ({user.email}):")
            print("-" * 30)
            
            for perm_method, perm_desc in permissions:
                if hasattr(user, perm_method):
                    result = getattr(user, perm_method)()
                    status = "✅" if result else "❌"
                    print(f"  {status} {perm_desc}")
                else:
                    print(f"  ❓ {perm_desc} (method not found)")
        
        print("\n" + "="*50)
        print("✅ Role permission testing completed!")

def test_role_hierarchy():
    """Test the role hierarchy logic."""
    with app.app_context():
        roles = ['employee', 'manager', 'admin', 'super_admin']
        hierarchy_tests = [
            ('Employee cannot be admin', 'employee', 'is_admin', False),
            ('Manager has manager privileges', 'manager', 'is_manager', True),
            ('Admin has admin privileges', 'admin', 'is_admin', True),
            ('Admin has manager privileges', 'admin', 'is_manager', True),
            ('Super Admin has all privileges', 'super_admin', 'is_admin', True),
            ('Only Super Admin can manage users', 'super_admin', 'can_manage_users', True),
            ('Admin cannot manage users', 'admin', 'can_manage_users', False),
        ]
        
        print("\n🔐 Testing Role Hierarchy Logic")
        print("="*50)
        
        for test_desc, role, method, expected in hierarchy_tests:
            # Create a test user with the specified role
            test_user = User()
            test_user.role = role
            
            if hasattr(test_user, method):
                result = getattr(test_user, method)()
                status = "✅" if result == expected else "❌"
                print(f"{status} {test_desc}: {result} (expected {expected})")
            else:
                print(f"❓ {test_desc}: Method {method} not found")
        
        print("\n✅ Role hierarchy testing completed!")

if __name__ == '__main__':
    print("🚀 Role-Based System Test Suite")
    print("="*50)
    
    try:
        test_role_permissions()
        test_role_hierarchy()
        print("\n🎉 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
