#!/usr/bin/env python3
"""
Production database setup script for Google Cloud deployment
Run this once after deployment to initialize the database with sample data
"""

import os
import sys
from app import create_app, db

def setup_production_database():
    """Set up the production database with initial data"""
    
    print("🚀 Setting up production database...")
    
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created")
        
        # Import models
        from app.models import User, Customer, Service, BusinessSettings, SMSSettings
        
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@laundry.com').first()
        if not admin:
            print("👤 Creating admin user...")
            admin = User()
            admin.email = 'admin@laundry.com'
            admin.full_name = 'System Administrator'
            admin.phone = '09123456789'
            admin.role = 'Super Admin'
            admin.is_active = True
            admin.set_password('admin123')  # Change this password after deployment!
            db.session.add(admin)
            
            # Create sample manager
            manager = User()
            manager.email = 'manager@laundry.com'
            manager.full_name = 'Store Manager'
            manager.phone = '09123456788'
            manager.role = 'Manager'
            manager.is_active = True
            manager.set_password('manager123')
            db.session.add(manager)
            
            print("✅ Created admin and manager users")
        else:
            print("ℹ️  Admin user already exists")
        
        # Check business settings
        business = BusinessSettings.query.first()
        if not business:
            print("🏢 Creating business settings...")
            business = BusinessSettings()
            business.business_name = 'Professional Laundry Service'
            business.business_tagline = 'Quality Cleaning Solutions'
            business.phone = '09123456789'
            business.email = 'info@laundry.com'
            business.address = 'Your Business Address Here'
            business.operating_hours = 'Mon-Sat: 7AM-8PM, Sun: 8AM-6PM'
            business.footer_text = 'Quality service you can trust'
            db.session.add(business)
            print("✅ Created business settings")
        else:
            print("ℹ️  Business settings already exist")
        
        # Check SMS settings
        sms_settings = SMSSettings.query.first()
        if not sms_settings:
            print("📱 Creating SMS settings...")
            sms_settings = SMSSettings()
            db.session.add(sms_settings)
            print("✅ Created SMS settings")
        else:
            print("ℹ️  SMS settings already exist")
        
        # Create sample customers
        customer_count = Customer.query.count()
        if customer_count == 0:
            print("👥 Creating sample customers...")
            customers = [
                {
                    'full_name': 'John Doe',
                    'email': 'john@example.com',
                    'phone': '09111111111',
                    'address': 'Sample Address 1',
                    'is_active': True
                },
                {
                    'full_name': 'Jane Smith',
                    'email': 'jane@example.com',
                    'phone': '09222222222',
                    'address': 'Sample Address 2',
                    'is_active': True
                },
                {
                    'full_name': 'Bob Wilson',
                    'email': 'bob@example.com',
                    'phone': '09333333333',
                    'address': 'Sample Address 3',
                    'is_active': True
                }
            ]
            
            for customer_data in customers:
                customer = Customer()
                customer.full_name = customer_data['full_name']
                customer.email = customer_data['email']
                customer.phone = customer_data['phone']
                customer.address = customer_data['address']
                customer.is_active = customer_data['is_active']
                db.session.add(customer)
            
            print("✅ Created sample customers")
        else:
            print(f"ℹ️  {customer_count} customers already exist")
        
        # Create sample services
        service_count = Service.query.count()
        if service_count == 0:
            print("🧺 Creating sample services...")
            services = [
                {'name': 'Wash & Dry', 'price': 50.0, 'description': 'Basic wash and dry service'},
                {'name': 'Wash, Dry & Fold', 'price': 70.0, 'description': 'Complete wash, dry and folding service'},
                {'name': 'Dry Cleaning', 'price': 150.0, 'description': 'Professional dry cleaning service'},
                {'name': 'Ironing Only', 'price': 30.0, 'description': 'Ironing service only'}
            ]
            
            for service_data in services:
                service = Service()
                service.name = service_data['name']
                service.price = service_data['price']
                service.description = service_data['description']
                service.is_active = True
                db.session.add(service)
            
            print("✅ Created sample services")
        else:
            print(f"ℹ️  {service_count} services already exist")
        
        # Commit all changes
        try:
            db.session.commit()
            print("🎉 Production database setup complete!")
            print()
            print("📋 Default Login Credentials:")
            print("🔐 Admin: admin@laundry.com / admin123")
            print("🔐 Manager: manager@laundry.com / manager123")
            print()
            print("⚠️  IMPORTANT: Change these passwords after first login!")
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = setup_production_database()
    sys.exit(0 if success else 1)
