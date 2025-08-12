from app import create_app, db
from app.models import Customer

def create_sample_customers():
    app = create_app()
    with app.app_context():
        # Check if customers already exist
        existing = Customer.query.first()
        if existing:
            print("Sample customers already exist")
            print(f"Total customers: {Customer.query.count()}")
            return
        
        # Create sample customers
        customers_data = [
            {'name': 'Maria Santos', 'email': 'maria@email.com', 'phone': '09171234567'},
            {'name': 'Juan Dela Cruz', 'email': 'juan@email.com', 'phone': '09281234567'},
            {'name': 'Ana Garcia', 'email': 'ana@email.com', 'phone': '09351234567'},
            {'name': 'Carlos Mendoza', 'email': 'carlos@email.com', 'phone': '09461234567'},
            {'name': 'Sofia Reyes', 'email': 'sofia@email.com', 'phone': '09171234568'},
            {'name': 'Roberto Cruz', 'email': 'roberto@email.com', 'phone': '09123456789'},
            {'name': 'Elena Flores', 'email': 'elena@email.com', 'phone': '09234567890'},
        ]
        
        for data in customers_data:
            customer = Customer(**data)
            db.session.add(customer)
        
        db.session.commit()
        print(f"Created {len(customers_data)} sample customers")
        
        # Display created customers
        customers = Customer.query.all()
        print("\nSample customers created:")
        for customer in customers:
            print(f"- {customer.name} ({customer.phone})")

if __name__ == '__main__':
    create_sample_customers()
