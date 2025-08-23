from faker import Faker

from app import create_app, db
from app.models import Customer

app = create_app()

fake = Faker()


def seed_customers(n=5000):
    from datetime import datetime

    for _ in range(n):
        full_name = fake.name()
        phone_number = fake.phone_number()
        email = fake.email()
        customer = Customer(
            full_name=full_name,
            phone=phone_number,
            email=email,
            is_active=True,
            date_created=datetime.utcnow(),
        )
        db.session.add(customer)
    db.session.commit()
    print(f"Seeded {n} customers.")


if __name__ == "__main__":
    with app.app_context():
        seed_customers()
