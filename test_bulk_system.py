from app import create_app
from app.models import Customer, BulkMessageHistory

def test_bulk_system():
    app = create_app()
    with app.app_context():
        customers = Customer.query.all()
        campaigns = BulkMessageHistory.query.all()
        
        print("=== BULK SMS SYSTEM STATUS ===")
        print(f"✅ Total customers: {len(customers)}")
        print(f"📱 Customers with phones: {len([c for c in customers if c.phone])}")
        print(f"📊 Previous campaigns: {len(campaigns)}")
        print()
        
        if customers:
            print("📋 Customer List:")
            for c in customers:
                phone_status = c.phone if c.phone else "No phone"
                print(f"  - {c.full_name}: {phone_status}")
        
        print("\n🚀 BULK MESSAGING READY!")
        print("   Navigate to: http://127.0.0.1:5000/sms-settings/bulk-message")

if __name__ == '__main__':
    test_bulk_system()
