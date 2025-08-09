#!/usr/bin/env python3

from app import create_app, db
from app.models import Laundry

app = create_app()

def debug_recent_laundries():
    with app.app_context():
        print("=== DEBUG: Recent Laundries for Dashboard ===")
        
        # Get recent laundries exactly as in the dashboard route
        recent_laundries = Laundry.query.order_by(Laundry.date_received.desc()).limit(5).all()
        
        print(f"Found {len(recent_laundries)} recent laundries")
        print()
        
        for i, laundry in enumerate(recent_laundries, 1):
            print(f"Laundry #{i}:")
            print(f"  ID: {laundry.id}")
            print(f"  Customer: {laundry.customer.full_name if laundry.customer else 'None'}")
            print(f"  Service: {laundry.service.name if laundry.service else laundry.service_type}")
            print(f"  Date Received: {laundry.date_received}")
            print(f"  Status: {laundry.status}")
            print(f"  Price: ₱{laundry.price:.2f}")
            print()
            
        if not recent_laundries:
            print("No laundries found in the database!")
            
            # Check if there are any laundries at all
            total_laundries = Laundry.query.count()
            print(f"Total laundries in database: {total_laundries}")

if __name__ == "__main__":
    debug_recent_laundries()
