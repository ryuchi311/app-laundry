#!/usr/bin/env python3
"""
Migration script to update role system from 'user' to 'employee' 
and create sample users for different roles
"""

import sys
import os
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

def update_existing_roles() -> None:
    """Update existing 'user' roles to 'employee'"""
    with app.app_context():
        # Update existing users with 'user' role to 'employee'
        users_updated = User.query.filter_by(role='user').update({User.role: 'employee'})
        
        print(f"Updated {users_updated} users from 'user' to 'employee' role")
        
        # Commit the changes
        db.session.commit()
        print("Role migration completed successfully!")

def create_sample_users() -> None:
    """Create sample users for different roles"""
    with app.app_context():
        sample_users: List[Dict[str, str]] = [
            {
                'email': 'superadmin@laundry.com',
                'password': 'admin123',
                'full_name': 'Super Administrator',
                'phone': '555-0001',
                'role': 'super_admin'
            },
            {
                'email': 'admin@laundry.com', 
                'password': 'admin123',
                'full_name': 'System Administrator',
                'phone': '555-0002',
                'role': 'admin'
            },
            {
                'email': 'manager@laundry.com',
                'password': 'manager123',
                'full_name': 'Operations Manager',
                'phone': '555-0003',
                'role': 'manager'
            },
            {
                'email': 'employee1@laundry.com',
                'password': 'employee123',
                'full_name': 'Laundry Employee 1',
                'phone': '555-0004',
                'role': 'employee'
            },
            {
                'email': 'employee2@laundry.com',
                'password': 'employee123',
                'full_name': 'Laundry Employee 2',
                'phone': '555-0005',
                'role': 'employee'
            }
        ]
        
        for user_data in sample_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email']).first()
            if not existing_user:
                # Create new user with explicit attribute assignment
                new_user = User()
                new_user.email = user_data['email']
                new_user.password = generate_password_hash(user_data['password'], method='pbkdf2:sha256')
                new_user.full_name = user_data['full_name']
                new_user.phone = user_data['phone']
                new_user.role = user_data['role']
                
                db.session.add(new_user)
                print(f"Created {user_data['role']}: {user_data['email']}")
            else:
                print(f"User already exists: {user_data['email']}")
        
        db.session.commit()
        print("Sample users creation completed!")

def display_role_permissions() -> None:
    """Display the role hierarchy and permissions"""
    permissions: Dict[str, List[str]] = {
        'super_admin': [
            'Full system access',
            'User management', 
            'Financial reports',
            'System settings',
            'All operational tasks'
        ],
        'admin': [
            'Full operational access',
            'Financial reports',
            'Expense management',
            'Inventory management',
            'Service management'
        ],
        'manager': [
            'Operational oversight',
            'Revenue visibility',
            'Inventory monitoring',
            'Service management',
            'Staff coordination'
        ],
        'employee': [
            'Process laundry orders',
            'Customer assistance',
            'Basic service access',
            'Order tracking'
        ]
    }
    
    print("\n" + "="*50)
    print("ROLE-BASED PERMISSION SYSTEM")
    print("="*50)
    
    for role, perms in permissions.items():
        print(f"\n{role.replace('_', ' ').title()}:")
        for perm in perms:
            print(f"  • {perm}")
    
    print("\n" + "="*50)
    print("LOGIN CREDENTIALS:")
    print("="*50)
    print("Super Admin: superadmin@laundry.com / admin123")
    print("Admin: admin@laundry.com / admin123") 
    print("Manager: manager@laundry.com / manager123")
    print("Employee 1: employee1@laundry.com / employee123")
    print("Employee 2: employee2@laundry.com / employee123")
    print("="*50)

if __name__ == '__main__':
    print("Starting role system migration...")
    
    # Update existing roles
    update_existing_roles()
    
    # Create sample users
    create_sample_users()
    
    # Display information
    display_role_permissions()
    
    print("\n🎉 Role system migration completed successfully!")
    print("You can now test different role permissions by logging in with the sample accounts.")
