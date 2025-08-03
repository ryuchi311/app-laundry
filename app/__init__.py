from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from os import path
from datetime import datetime

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

@login_manager.user_loader
def load_user(id):
    from .models import User
    return User.query.get(int(id))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///laundry.db'
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Configure for your email provider
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = ''  # Add your email
    app.config['MAIL_PASSWORD'] = ''  # Add your password

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    from .views import views
    from .auth import auth
    from .customer import customer
    from .order import order

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(customer, url_prefix='/customer')
    app.register_blueprint(order, url_prefix='/order')

    from .models import User, Customer, Order

    create_database(app)

    return app

def create_database(app):
    if not path.exists('app/laundry.db'):
        with app.app_context():
            db.create_all()
            print('Created Database!')
