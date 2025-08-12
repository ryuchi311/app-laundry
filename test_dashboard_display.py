#!/usr/bin/env python3

from app import create_app, db
from app.models import Laundry

app = create_app()

def test_dashboard_display():
    with app.app_context():
        print("=== Testing Dashboard Display Format ===")
        
        recent_laundries = Laundry.query.order_by(Laundry.date_received.desc()).limit(5).all()
        
        print(f"Found {len(recent_laundries)} recent laundries")
        print()
        
        for i, laundry in enumerate(recent_laundries, 1):
            print(f"Dashboard Display #{i}:")
            print(f"  Customer: {laundry.customer.full_name}")
            print(f"  ID Display: #{laundry.laundry_id} • {laundry.get_service_name()}")
            print(f"  Date: {laundry.date_received.strftime('%b %d, %Y at %I:%M %p')}")
            print(f"  Status: {laundry.status}")
            print(f"  Price: ₱{laundry.price:.2f}")
            print()

if __name__ == "__main__":
    test_dashboard_display()
