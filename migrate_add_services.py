"""
Migration script to add Service model and update Order model
"""
from app import create_app, db
from app.models import Service, Order

def create_service_table():
    """Create the Service table and populate with default services"""
    
    app = create_app()
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            
            # Check if services already exist
            if Service.query.count() == 0:
                # Create default services based on the legacy pricing
                default_services = [
                    {
                        'name': 'Wash Only',
                        'description': 'Professional washing service for your clothes',
                        'base_price': 150.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-tint',
                        'category': 'Standard',
                        'estimated_hours': 6
                    },
                    {
                        'name': 'Dry Only',
                        'description': 'High-quality drying service',
                        'base_price': 120.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-wind',
                        'category': 'Standard',
                        'estimated_hours': 4
                    },
                    {
                        'name': 'Wash & Dry',
                        'description': 'Complete wash and dry service',
                        'base_price': 200.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-tshirt',
                        'category': 'Standard',
                        'estimated_hours': 8
                    },
                    {
                        'name': 'Wash & Fold',
                        'description': 'Wash, dry, and fold service with care',
                        'base_price': 250.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-layer-group',
                        'category': 'Premium',
                        'estimated_hours': 12
                    },
                    {
                        'name': 'Full Service',
                        'description': 'Complete laundry service: wash, dry, fold, and iron',
                        'base_price': 300.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-star',
                        'category': 'Premium',
                        'estimated_hours': 24
                    },
                    {
                        'name': 'Iron Only',
                        'description': 'Professional ironing and pressing service',
                        'base_price': 100.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-fire',
                        'category': 'Specialty',
                        'estimated_hours': 3
                    },
                    {
                        'name': 'Express Wash & Dry',
                        'description': 'Fast same-day wash and dry service',
                        'base_price': 280.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-bolt',
                        'category': 'Express',
                        'estimated_hours': 4
                    },
                    {
                        'name': 'Delicate Care',
                        'description': 'Special care for delicate fabrics and garments',
                        'base_price': 350.0,
                        'price_per_kg': 0.0,
                        'icon': 'fas fa-heart',
                        'category': 'Specialty',
                        'estimated_hours': 18
                    }
                ]
                
                for service_data in default_services:
                    service = Service(**service_data)
                    db.session.add(service)
                
                db.session.commit()
                print(f"✅ Created {len(default_services)} default services")
            else:
                print("⚠️  Services already exist, skipping default service creation")
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    create_service_table()
