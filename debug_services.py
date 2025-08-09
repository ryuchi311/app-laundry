#!/usr/bin/env python3

from app import create_app, db
from app.models import Laundry, Service

app = create_app()

def debug_services():
    with app.app_context():
        print("=== DEBUG: Services and Laundry Service Relations ===")
        
        # Check services
        services = Service.query.all()
        print(f"Found {len(services)} services:")
        for service in services:
            print(f"  Service ID: {service.id}, Name: {service.name}")
        print()
        
        # Check laundries and their service relations
        laundries = Laundry.query.all()
        print(f"Found {len(laundries)} laundries:")
        for laundry in laundries:
            print(f"  Laundry ID: {laundry.id}")
            print(f"    service_id: {laundry.service_id}")
            print(f"    service_type: {laundry.service_type}")
            print(f"    service object: {laundry.service}")
            if laundry.service:
                print(f"    service name: {laundry.service.name}")
            print()

if __name__ == "__main__":
    debug_services()
