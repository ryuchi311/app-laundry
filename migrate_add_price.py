#!/usr/bin/env python3
"""
Database migration script to add price column to Order table and calculate prices.
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Order

def migrate_add_price_column():
    """Add price column and calculate prices for existing orders"""
    app = create_app()
    
    with app.app_context():
        # Check if price column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('order')]
        
        if 'price' not in columns:
            print("Adding price column to Order table...")
            # Add the price column
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE "order" ADD COLUMN price FLOAT DEFAULT 0.0'))
                conn.commit()
            print("✓ Price column added successfully")
        else:
            print("Price column already exists")
        
        # Update prices for all existing orders
        print("Calculating prices for existing orders...")
        orders = Order.query.all()
        updated_count = 0
        
        for order in orders:
            old_price = order.price
            order.update_price()
            if order.price != old_price:
                updated_count += 1
        
        db.session.commit()
        print(f"✓ Updated prices for {updated_count} orders")
        print(f"Total orders processed: {len(orders)}")

if __name__ == "__main__":
    migrate_add_price_column()
