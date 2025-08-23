from app import db
from app.models import User
from main import app

email_to_update = "employee2@laundry.com"
with app.app_context():
    user = User.query.filter_by(email=email_to_update).first()
    if user:
        user.role = "user"
        user.is_active = True
        db.session.commit()
        print(f"Updated {email_to_update} to role 'user' and set active.")
    else:
        print(f"User with email {email_to_update} not found.")
