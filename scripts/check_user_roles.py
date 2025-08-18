from app import db
from app.models import User
from main import app

emails = ['employee1@laundry.com', 'employee2@laundry.com']
with app.app_context():
    for email in emails:
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"{email}: role={user.role}, active={user.is_active}")
        else:
            print(f"User with email {email} not found.")
