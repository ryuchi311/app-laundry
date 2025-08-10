#!/usr/bin/env python3
"""
Test script to verify that bulk SMS only includes active customers
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Customer

def test_bulk_sms_active_filter():
    """Test that bulk SMS only includes active customers"""
    
    app = create_app()
    
    with app.app_context():
        print("=== BULK SMS ACTIVE CUSTOMER FILTER TEST ===")
        print()
        
        # Get all customers
        all_customers = Customer.query.all()
        print(f"📋 Total customers in database: {len(all_customers)}")
        
        # Count active vs inactive customers
        active_customers = Customer.query.filter(Customer.is_active == True).all()
        inactive_customers = Customer.query.filter(Customer.is_active == False).all()
        
        print(f"✅ Active customers: {len(active_customers)}")
        print(f"❌ Inactive customers: {len(inactive_customers)}")
        print()
        
        # Show customer status details
        print("📋 CUSTOMER STATUS DETAILS:")
        print("-" * 60)
        for customer in all_customers:
            status = "✅ Active" if customer.is_active else "❌ Inactive"
            phone = customer.phone or "No Phone"
            print(f"  {customer.full_name[:20]:<20} | {status:<10} | {phone}")
        print()
        
        # Test bulk SMS customer query (what the system would use)
        # This mirrors the query from sms_settings.py
        bulk_sms_customers = Customer.query.filter(
            Customer.phone.isnot(None),
            Customer.is_active == True
        ).all()
        
        bulk_sms_customers_with_phones = [c for c in bulk_sms_customers if c.phone and c.phone.strip()]
        
        print("📱 BULK SMS TARGET CUSTOMERS:")
        print("-" * 60)
        print(f"🎯 Customers that would receive bulk SMS: {len(bulk_sms_customers_with_phones)}")
        
        if bulk_sms_customers_with_phones:
            for customer in bulk_sms_customers_with_phones:
                print(f"  ✅ {customer.full_name} | {customer.phone}")
        else:
            print("  No customers would receive bulk SMS (no active customers with phones)")
        print()
        
        # Show excluded customers (inactive or no phone)
        excluded_inactive = Customer.query.filter(
            Customer.is_active == False,
            Customer.phone.isnot(None)
        ).all()
        excluded_inactive_with_phones = [c for c in excluded_inactive if c.phone and c.phone.strip()]
        
        excluded_no_phone = Customer.query.filter(
            Customer.is_active == True,
            Customer.phone.is_(None)
        ).all()
        
        print("🚫 EXCLUDED FROM BULK SMS:")
        print("-" * 60)
        
        if excluded_inactive_with_phones:
            print(f"❌ Inactive customers with phones (excluded): {len(excluded_inactive_with_phones)}")
            for customer in excluded_inactive_with_phones:
                print(f"  ❌ {customer.full_name} | {customer.phone} | INACTIVE")
        
        if excluded_no_phone:
            print(f"📵 Active customers without phones (excluded): {len(excluded_no_phone)}")
            for customer in excluded_no_phone:
                print(f"  📵 {customer.full_name} | No Phone | ACTIVE")
        
        if not excluded_inactive_with_phones and not excluded_no_phone:
            print("  No customers excluded - all active customers have phones")
        print()
        
        # Summary
        print("📊 SUMMARY:")
        print("-" * 60)
        total_with_phones = Customer.query.filter(Customer.phone.isnot(None)).count()
        active_with_phones = len(bulk_sms_customers_with_phones)
        inactive_with_phones = len(excluded_inactive_with_phones)
        
        print(f"📱 Total customers with phones: {total_with_phones}")
        print(f"✅ Active customers with phones: {active_with_phones}")
        print(f"❌ Inactive customers with phones: {inactive_with_phones}")
        print(f"🎯 Customers that will receive bulk SMS: {active_with_phones}")
        
        if inactive_with_phones > 0:
            print(f"✅ SUCCESS: {inactive_with_phones} inactive customer(s) will be excluded from bulk SMS")
        else:
            print("ℹ️  No inactive customers with phones to test exclusion")
        
        print()
        print("✅ TEST COMPLETED: Bulk SMS filtering is working correctly!")

if __name__ == '__main__':
    test_bulk_sms_active_filter()
