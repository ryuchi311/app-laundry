#!/usr/bin/env python3

from app import create_app
from app.models import Laundry

app = create_app()

def check_laundry_ids():
    with app.app_context():
        print("=== Checking Laundry ID Values ===")
        
        laundries = Laundry.query.all()
        print(f"Found {len(laundries)} laundries:")
        
        for laundry in laundries:
            print(f"  Database ID: {laundry.id}")
            print(f"  Laundry ID: {laundry.laundry_id}")
            print(f"  Customer: {laundry.customer.full_name}")
            print()

if __name__ == "__main__":
    check_laundry_ids()
