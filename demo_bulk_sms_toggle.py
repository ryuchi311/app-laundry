#!/usr/bin/env python3
"""
Demo script to show how customer status affects bulk SMS targeting
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Customer

def demo_status_toggle():
    """Demo toggling customer status and seeing effect on bulk SMS count"""
    
    app = create_app()
    
    with app.app_context():
        print("=== BULK SMS STATUS TOGGLE DEMO ===")
        print()
        
        # Find an active customer to demonstrate with
        active_customer = Customer.query.filter(
            Customer.is_active == True,
            Customer.phone.isnot(None)
        ).first()
        
        if not active_customer:
            print("No active customers with phones found for demo")
            return
        
        print(f"📱 Demo Customer: {active_customer.full_name}")
        print(f"   Phone: {active_customer.phone}")
        print(f"   Current Status: {'✅ Active' if active_customer.is_active else '❌ Inactive'}")
        print()
        
        # Check current bulk SMS count
        def get_bulk_sms_count():
            customers = Customer.query.filter(
                Customer.phone.isnot(None),
                Customer.is_active == True
            ).all()
            return len([c for c in customers if c.phone and c.phone.strip()])
        
        initial_count = get_bulk_sms_count()
        print(f"🎯 Current bulk SMS target count: {initial_count}")
        
        # Toggle status to inactive
        print("\n🔄 Toggling customer status to INACTIVE...")
        active_customer.is_active = False
        db.session.commit()
        
        new_count = get_bulk_sms_count()
        print(f"🎯 New bulk SMS target count: {new_count}")
        print(f"   Change: {new_count - initial_count} customer(s)")
        
        if new_count < initial_count:
            print("✅ SUCCESS: Customer excluded from bulk SMS when inactive")
        
        # Toggle status back to active
        print("\n🔄 Toggling customer status back to ACTIVE...")
        active_customer.is_active = True
        db.session.commit()
        
        final_count = get_bulk_sms_count()
        print(f"🎯 Final bulk SMS target count: {final_count}")
        print(f"   Change: {final_count - new_count} customer(s)")
        
        if final_count > new_count:
            print("✅ SUCCESS: Customer included in bulk SMS when active")
        
        print()
        print("✅ DEMO COMPLETED: Customer status correctly affects bulk SMS targeting!")

if __name__ == '__main__':
    demo_status_toggle()
