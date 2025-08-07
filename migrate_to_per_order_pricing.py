#!/usr/bin/env python3
"""
Database migration script to update pricing from per-item to per-laundry.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Laundry

def migrate_to_per_laundry_pricing():
    """Update existing laundries to use per-laundry pricing instead of per-item"""
    app = create_app()
    
    with app.app_context():
        print("Updating existing laundries to per-laundry pricing...")
        laundries = Laundry.query.all()
        updated_count = 0
        
        for laundry in laundries:
            old_price = laundry.price
            # Recalculate using the new per-laundry pricing
            laundry.update_price()
            if laundry.price != old_price:
                updated_count += 1
                print(f"Laundry {laundry.laundry_id}: {laundry.service_type} - Updated from ₱{old_price:.2f} to ₱{laundry.price:.2f}")
        
        db.session.commit()
        print(f"✓ Updated prices for {updated_count} laundries")
        print(f"Total laundries processed: {len(laundries)}")
        
        # Show summary of current pricing
        print("\n--- Current Per-Laundry Pricing ---")
        from app.models import Service
        services = Service.query.filter_by(is_active=True).all()
        for service in services:
            print(f"{service.name}: ₱{service.price_per_kg}/kg")

if __name__ == "__main__":
    migrate_to_per_laundry_pricing()
