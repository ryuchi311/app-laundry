from app import create_app, db
from app.models import User, Customer, Laundry

app = create_app()
with app.app_context():
    print(f'Users: {User.query.count()}')
    print(f'Customers: {Customer.query.count()}')
    print(f'Orders: {Laundry.query.count()}')