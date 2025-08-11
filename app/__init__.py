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
    
    # Configure app for different environments
    if os.environ.get('GAE_ENV', '').startswith('standard'):
        # Running on Google App Engine
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret-key-change-this')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/laundry.db'
        app.config['DEBUG'] = False
        print("🚀 Running in Google Cloud Production Environment")
    else:
        # Running locally
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laundry.db'
        app.config['DEBUG'] = True
        print("🔧 Running in Local Development Environment")
    
    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
    
    # SMS Configuration (Environment variables)
    app.config['SEMAPHORE_API_KEY'] = os.environ.get('SEMAPHORE_API_KEY', '')
    app.config['SEMAPHORE_SENDER_NAME'] = os.environ.get('SEMAPHORE_SENDER_NAME', 'ACCIO Laundry')
    
    # Database configuration
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    from .business_settings import business_settings_bp

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
    app.register_blueprint(business_settings_bp)

    from .models import User, Customer, Laundry, Service, InventoryItem, InventoryCategory, StockMovement, Expense, ExpenseCategory, SalesReport, LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, SMSSettings, BulkMessageHistory, Notification, BusinessSettings
    
    # Context processor to make business settings available globally
    @app.context_processor
    def inject_business_settings():
        return dict(business_settings=BusinessSettings.get_settings())

    create_database(app)

    return app

def create_database(app):
    # Determine database path based on environment
    if os.environ.get('GAE_ENV', '').startswith('standard'):
        # Production on Google Cloud
        db_path = 'instance/laundry.db'
        if not os.path.exists('instance'):
            os.makedirs('instance', exist_ok=True)
    else:
        # Local development
        db_path = 'laundry.db'
    
    if not path.exists(db_path):
        with app.app_context():
            db.create_all()
            print(f'✅ Created Database at {db_path}!')
            
            # Create default admin user for production
            from .models import User, BusinessSettings
            
            # Check if admin user already exists
            admin = User.query.filter_by(email='admin@laundry.com').first()
            if not admin:
                admin = User()
                admin.email = 'admin@laundry.com'
                admin.full_name = 'System Administrator'
                admin.phone = '09123456789'
                admin.role = 'Super Admin'
                admin.set_password('admin123')  # Change this after first login!
                db.session.add(admin)
                print('✅ Created default admin user')
            
            # Create default business settings
            business = BusinessSettings.query.first()
            if not business:
                business = BusinessSettings()
                business.business_name = 'Professional Laundry Service'
                business.business_tagline = 'Quality Cleaning Solutions'
                business.phone = '09123456789'
                business.email = 'info@laundry.com'
                business.address = 'Your Business Address Here'
                business.operating_hours = 'Mon-Sat: 7AM-8PM, Sun: 8AM-6PM'
                business.footer_text = 'Quality service you can trust'
                db.session.add(business)
                print('✅ Created default business settings')
            
            # Create default SMS settings
            from .models import SMSSettings
            existing_settings = SMSSettings.query.first()
            if not existing_settings:
                default_settings = SMSSettings()
                db.session.add(default_settings)
                print('✅ Created default SMS settings')
                
            db.session.commit()
            print('🎉 Database initialization complete!')
