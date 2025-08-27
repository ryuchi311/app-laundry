import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*")


@login_manager.user_loader
def load_user(id):
    from .models import User

    return User.query.get(int(id))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "your-secret-key"
    )  # Change this in production
    # Allow overriding the database via DATABASE_URL (e.g., Cloud SQL)
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        db_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "instance", "laundry.db")
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Configure for your email provider
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")  # Add your email
    app.config["MAIL_PASSWORD"] = os.environ.get(
        "MAIL_PASSWORD", ""
    )  # Add your password

    # SMS Configuration (Environment variables)
    app.config["SEMAPHORE_API_KEY"] = os.environ.get("SEMAPHORE_API_KEY", "")
    app.config["SEMAPHORE_SENDER_NAME"] = os.environ.get(
        "SEMAPHORE_SENDER_NAME", "ACCIO Laundry"
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore
    mail.init_app(app)
    socketio.init_app(app)

    from .auth import auth
    from .business_settings import business_settings_bp
    from .customer import customer
    from .expenses import expenses_bp
    from .inventory import inventory
    from .laundry import laundry
    from .loyalty import loyalty_bp
    from .notifications import notifications
    from .profile import profile
    from .service import service
    from .sms_settings import sms_settings_bp
    from .user_management import user_management
    from .views import views

    app.register_blueprint(views, url_prefix="/")
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(customer, url_prefix="/customer")
    app.register_blueprint(laundry, url_prefix="/laundry")
    app.register_blueprint(service, url_prefix="/service")
    app.register_blueprint(profile, url_prefix="/profile")
    app.register_blueprint(inventory, url_prefix="/inventory")
    app.register_blueprint(expenses_bp, url_prefix="/expenses")
    app.register_blueprint(loyalty_bp, url_prefix="/loyalty")
    app.register_blueprint(sms_settings_bp, url_prefix="/sms-settings")
    app.register_blueprint(notifications)
    app.register_blueprint(user_management, url_prefix="/admin/users")
    app.register_blueprint(business_settings_bp)

    # Import only the model needed at app startup to avoid unused-import noise
    from .models import BusinessSettings

    # Context processor to make business settings available globally
    @app.context_processor
    def inject_business_settings():
        return dict(business_settings=BusinessSettings.get_settings())


    # Avoid running the runtime DB creation/seeding when pytest is running
    import sys

    running_under_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST")) or any(
        "pytest" in str(a) for a in sys.argv
    )

    if not running_under_pytest:
        create_database(app)

    return app


def create_database(app):
    # Always ensure all tables exist (safe: create_all creates missing tables only)
    with app.app_context():
        db.create_all()

        # If we're running tests, avoid seeding or performing runtime migrations
        # to prevent interference with test-managed databases.
        import os

        if app.config.get("TESTING") or os.environ.get("PYTEST_CURRENT_TEST"):
            return

        # Ensure the 'must_change_password' column exists on the user table.
        # For SQLite, ALTER TABLE ADD COLUMN is supported for adding a simple column.
        try:
            from sqlalchemy import text

            inspector = db.inspect(db.engine)
            cols = [c["name"] for c in inspector.get_columns("user")]
            if "must_change_password" not in cols:
                # Add the column (SQLite uses INTEGER for booleans)
                db.session.execute(text("ALTER TABLE user ADD COLUMN must_change_password BOOLEAN DEFAULT 0"))
                db.session.commit()
                print("Added missing column 'must_change_password' to user table.")
        except Exception:
            # If migration fails, continue; the app can still run but tests may fail
            pass

        # Ensure default SMS settings exist
        from .models import SMSSettings

        existing_settings = SMSSettings.query.first()
        if not existing_settings:
            default_settings = SMSSettings()
            db.session.add(default_settings)
            db.session.commit()
            print("Created default SMS settings!")

        # Ensure at least one SMS settings profile exists (seed from active settings)
        from .models import SMSSettingsProfile

        try:
            if SMSSettingsProfile.query.count() == 0:
                # create_from_active returns an instance but we don't need to keep it here
                SMSSettingsProfile.create_from_active("Default", user_id=None, make_default=True)
                db.session.commit()
                print("Created default SMS settings profile!")
        except Exception as e:
            # Do not block app startup if seeding fails; just log
            print(f"Warning: could not seed SMS settings profile: {e}")

        # Ensure there's at least one super admin account. If none exists create one
        # using environment variables so deployments can set secure defaults.
        try:
            from .models import User
            from werkzeug.security import generate_password_hash

            sa = User.query.filter_by(role="super_admin").first()
            if not sa:
                sa_email = os.environ.get("DEFAULT_SUPERADMIN_EMAIL", "admin@example.com")
                sa_password = os.environ.get("DEFAULT_SUPERADMIN_PASSWORD", "admin")
                new_sa = User()
                new_sa.email = sa_email
                new_sa.full_name = "Super Administrator"
                new_sa.role = "super_admin"
                new_sa.password = generate_password_hash(sa_password, method="pbkdf2:sha256")
                # Require password change on first login
                new_sa.must_change_password = True
                db.session.add(new_sa)
                db.session.commit()
                print(
                    f"Created default super-admin account: {sa_email}.\n"
                    "Password was taken from DEFAULT_SUPERADMIN_PASSWORD or default 'admin'.\n"
                    "Change this password immediately after first login."
                )
        except Exception as e:
            print(f"Warning: could not create default super-admin: {e}")
