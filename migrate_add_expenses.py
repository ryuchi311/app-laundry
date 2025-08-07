#!/usr/bin/env python3
"""
Migration script to add Expense Management tables
Run this after adding the new models to add expense tracking functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import ExpenseCategory, Expense, SalesReport
from datetime import datetime

def migrate_add_expenses():
    app = create_app()
    
    with app.app_context():
        print("Adding Expense Management tables...")
        
        # Create the new tables
        db.create_all()
        
        # Add default expense categories
        default_categories = [
            {'name': 'Utilities', 'description': 'Electricity, water, internet, phone bills', 'color': '#F59E0B'},
            {'name': 'Rent', 'description': 'Shop rent, storage rent', 'color': '#EF4444'},
            {'name': 'Maintenance', 'description': 'Equipment maintenance, repairs', 'color': '#8B5CF6'},
            {'name': 'Supplies', 'description': 'Cleaning supplies, detergents, chemicals', 'color': '#10B981'},
            {'name': 'Insurance', 'description': 'Business insurance, equipment insurance', 'color': '#F97316'},
            {'name': 'Marketing', 'description': 'Advertising, promotional materials', 'color': '#06B6D4'},
            {'name': 'Transportation', 'description': 'Fuel, vehicle maintenance, delivery costs', 'color': '#84CC16'},
            {'name': 'Professional Services', 'description': 'Accounting, legal, consulting fees', 'color': '#6366F1'},
            {'name': 'Miscellaneous', 'description': 'Other business expenses', 'color': '#6B7280'},
        ]
        
        for cat_data in default_categories:
            existing = ExpenseCategory.query.filter_by(name=cat_data['name']).first()
            if not existing:
                category = ExpenseCategory(**cat_data)
                db.session.add(category)
                print(f"Added category: {cat_data['name']}")
        
        try:
            db.session.commit()
            print("✅ Migration completed successfully!")
            print("📊 Expense Management system is now ready to use")
            print("\nDefault expense categories added:")
            for cat in default_categories:
                print(f"  • {cat['name']}: {cat['description']}")
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    if migrate_add_expenses():
        print("\n🎉 You can now access Expense Management at: /expenses")
        print("   Features available:")
        print("   • Track business expenses by category")
        print("   • Monitor rent, utilities, maintenance costs")
        print("   • Generate sales and expense reports")
        print("   • Set up recurring expenses")
        print("   • Calculate profit margins")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
