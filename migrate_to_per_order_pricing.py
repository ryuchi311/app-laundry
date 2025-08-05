#!/usr/bin/env python3
"""
Database migration script to update pricing from per-item to per-order.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Order

def migrate_to_per_order_pricing():
    """Update existing orders to use per-order pricing instead of per-item"""
    app = create_app()
    
    with app.app_context():
        print("Updating existing orders to per-order pricing...")
        orders = Order.query.all()
        updated_count = 0
        
        for order in orders:
            old_price = order.price
            # Recalculate using the new per-order pricing
            order.update_price()
            if order.price != old_price:
                updated_count += 1
                print(f"Order {order.order_id}: {order.service_type} - Updated from ₱{old_price:.2f} to ₱{order.price:.2f}")
        
        db.session.commit()
        print(f"✓ Updated prices for {updated_count} orders")
        print(f"Total orders processed: {len(orders)}")
        
        # Show summary of current pricing
        print("\n--- Current Per-Order Pricing ---")
        for service, price in Order.PRICING.items():
            print(f"{service}: ₱{price}")

if __name__ == "__main__":
    migrate_to_per_order_pricing()
