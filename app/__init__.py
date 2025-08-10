from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from os import path
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(id):
    from .models import User
    return User.query.get(int(id))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')  # Change this in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laundry.db'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Configure for your email provider
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')  # Add your email
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')  # Add your password
    
    # SMS Configuration (Environment variables)
    app.config['SEMAPHORE_API_KEY'] = os.environ.get('SEMAPHORE_API_KEY', '')
    app.config['SEMAPHORE_SENDER_NAME'] = os.environ.get('SEMAPHORE_SENDER_NAME', 'ACCIO Laundry')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore
    mail.init_app(app)

    from .views import views
    from .auth import auth
    from .customer import customer
    from .laundry import laundry
    from .service import service
    from .profile import profile
    from .inventory import inventory
    from .expenses import expenses_bp
    from .loyalty import loyalty_bp
    from .sms_settings import sms_settings_bp
    from .notifications import notifications
    from .user_management import user_management

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(customer, url_prefix='/customer')
    app.register_blueprint(laundry, url_prefix='/laundry')
    app.register_blueprint(service, url_prefix='/service')
    app.register_blueprint(profile, url_prefix='/profile')
    app.register_blueprint(inventory, url_prefix='/inventory')
    app.register_blueprint(expenses_bp, url_prefix='/expenses')
    app.register_blueprint(loyalty_bp, url_prefix='/loyalty')
    app.register_blueprint(sms_settings_bp, url_prefix='/sms-settings')
    app.register_blueprint(notifications)
    app.register_blueprint(user_management, url_prefix='/admin/users')

    from .models import User, Customer, Laundry, Service, InventoryItem, InventoryCategory, StockMovement, Expense, ExpenseCategory, SalesReport, LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, SMSSettings, BulkMessageHistory, Notification

    create_database(app)

    return app

def create_database(app):
    if not path.exists('app/laundry.db'):
        with app.app_context():
            db.create_all()
            print('Created Database!')
            
            # Create default SMS settings
            from .models import SMSSettings
            existing_settings = SMSSettings.query.first()
            if not existing_settings:
                default_settings = SMSSettings()
                db.session.add(default_settings)
                db.session.commit()
                print('Created default SMS settings!')
