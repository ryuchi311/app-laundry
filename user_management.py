#!/usr/bin/env python3
"""
User creation utility for the laundry management system.
This script provides a clean interface for creating users with proper roles.
"""

import sys
import os
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()

def create_user(email: str, password: str, full_name: str, phone: str, role: str) -> Optional[User]:
    """
    Create a new user with the specified details.
    
    Args:
        email: User's email address (must be unique)
        password: User's password (will be hashed)
        full_name: User's full name
        phone: User's phone number
        role: User's role ('super_admin', 'admin', 'manager', 'employee')
    
    Returns:
        User object if created successfully, None if user already exists
    """
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ User with email '{email}' already exists!")
            return None
        
        # Validate role
        valid_roles = ['super_admin', 'admin', 'manager', 'employee']
        if role not in valid_roles:
            print(f"❌ Invalid role '{role}'. Must be one of: {', '.join(valid_roles)}")
            return None
        
        # Create new user
        new_user = User()
        new_user.email = email
        new_user.password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user.full_name = full_name
        new_user.phone = phone
        new_user.role = role
        new_user.is_active = True
        
        try:
            db.session.add(new_user)
            db.session.commit()
            print(f"✅ Successfully created {role}: {email}")
            return new_user
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating user: {e}")
            return None

def list_all_users() -> None:
    """List all users in the system with their roles."""
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the system.")
            return
        
        print("\n" + "="*70)
        print("ALL USERS IN THE SYSTEM")
        print("="*70)
        print(f"{'ID':<4} {'Email':<30} {'Name':<20} {'Role':<15}")
        print("-"*70)
        
        for user in users:
            print(f"{user.id:<4} {user.email:<30} {user.full_name:<20} {user.role:<15}")
        
        print("="*70)

def interactive_user_creation() -> None:
    """Interactive user creation with prompts."""
    print("\n🎯 Interactive User Creation")
    print("="*40)
    
    # Get user input
    email = input("Email address: ").strip()
    if not email:
        print("❌ Email is required!")
        return
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password is required!")
        return
    
    full_name = input("Full name: ").strip()
    if not full_name:
        print("❌ Full name is required!")
        return
    
    phone = input("Phone number: ").strip()
    
    print("\nAvailable roles:")
    roles = ['super_admin', 'admin', 'manager', 'employee']
    for i, role in enumerate(roles, 1):
        role_display = role.replace('_', ' ').title()
        print(f"  {i}. {role_display}")
    
    try:
        role_choice = int(input("\nSelect role (1-4): ")) - 1
        if 0 <= role_choice < len(roles):
            selected_role = roles[role_choice]
        else:
            print("❌ Invalid role selection!")
            return
    except ValueError:
        print("❌ Please enter a valid number!")
        return
    
    # Create the user
    user = create_user(email, password, full_name, phone, selected_role)
    if user:
        print(f"\n🎉 User created successfully!")
        print(f"Email: {user.email}")
        print(f"Role: {user.get_role_display()}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'list':
            list_all_users()
        elif command == 'create':
            interactive_user_creation()
        elif command == 'help':
            print("User Management Utility")
            print("======================")
            print("Usage:")
            print("  python user_management.py list     - List all users")
            print("  python user_management.py create   - Create a new user interactively")
            print("  python user_management.py help     - Show this help message")
        else:
            print("❌ Unknown command. Use 'help' to see available commands.")
    else:
        print("User Management Utility")
        print("Use 'python user_management.py help' for usage instructions")
