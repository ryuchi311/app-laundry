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
    # SQLAlchemy engine options to handle MySQL servers that drop idle
    # connections quickly (e.g., Hostinger with 1-5 minute idle timeout).
    # - pool_pre_ping: checks connection liveness before using it and reconnects if needed.
    # - pool_recycle: force recycling connections older than this many seconds.
    # Choose a recycle slightly shorter than the host idle timeout (4 minutes).
    app.config.setdefault(
        "SQLALCHEMY_ENGINE_OPTIONS",
        {
            "pool_pre_ping": True,
            "pool_recycle": 240,
            # keep conservative pool sizing; adjust if you know concurrency
            "pool_size": 5,
            "max_overflow": 10,
        },
    )
    import sys
    # Detect pytest/CI so we don't hardcode a DB URI and interfere with tests
    running_under_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST")) or any(
        "pytest" in str(a) for a in sys.argv
    )
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "your-secret-key"
    )  # Change this in production
    # Allow overriding the database via DATABASE_URL or connect.json (easier for orchestration).
    # When running under pytest, skip setting a default so tests can provide
    # their own temporary DB URI after create_app().
    database_url = os.environ.get("DATABASE_URL")
    # If a connect.json exists, prefer its values (it is written by the admin UI on save)
    try:
        connect_path = os.path.join(os.path.abspath(os.getcwd()), "connect.json")
        if os.path.exists(connect_path):
            import json

            with open(connect_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    # Only override if a value is present
                    database_url = data.get("DATABASE_URL") or database_url
                    # Also prefer SMS settings from connect.json
                    if data.get("SEMAPHORE_API_KEY"):
                        os.environ["SEMAPHORE_API_KEY"] = data.get("SEMAPHORE_API_KEY")
                    if data.get("SEMAPHORE_SENDER_NAME"):
                        os.environ["SEMAPHORE_SENDER_NAME"] = data.get("SEMAPHORE_SENDER_NAME")
                except Exception:
                    pass
    except Exception:
        pass
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    elif not running_under_pytest:
        db_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "instance", "laundry.db")
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    # When running under pytest and no DATABASE_URL is provided, set an
    # in-memory SQLite URI so Flask-SQLAlchemy can initialize without error.
    if running_under_pytest and not database_url:
        app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")

    # Ensure Flask knows it's in testing mode so runtime seeding/migrations
    # in create_database() are skipped during pytest runs.
    if running_under_pytest:
        app.config.setdefault("TESTING", True)
    # Use an explicit flag to control runtime seeding behavior. This is
    # more reliable than environment variables when create_database is
    # invoked during app startup under different runtimes. Default to
    # False for normal runtimes so the database schema is created on first
    # startup if missing; tests may set this flag or running_under_pytest
    # will keep runtime seeding disabled.
    app.config["_SKIP_RUNTIME_SEEDING"] = running_under_pytest

    # Common SQLAlchemy config
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config["MAIL_SERVER"] = "smtp.gmail.com"  # Configure for your email provider
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME", "")  # Add your email
    app.config["MAIL_PASSWORD"] = os.environ.get(
        "MAIL_PASSWORD", ""
    )  # Add your password

    # SMS Configuration (Environment variables or connect.json)
    app.config["SEMAPHORE_API_KEY"] = os.environ.get("SEMAPHORE_API_KEY", "")
    app.config["SEMAPHORE_SENDER_NAME"] = os.environ.get(
        "SEMAPHORE_SENDER_NAME", "ACCIO Laundry"
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # type: ignore
    mail.init_app(app)
    socketio.init_app(app)

    # Optionally enable lightweight request/SQL monitoring (controlled by env)
    try:
        from .monitoring import init_monitoring

        # Only enable if environment requests it, or when not running under pytest
        if os.environ.get("ENABLE_REQUEST_MONITORING") == "1" or not running_under_pytest:
            # Ensure we have an application context so SQL engine is available
            try:
                with app.app_context():
                    init_monitoring(app, db)
            except Exception:
                # If monitoring registration fails, log via print (avoid import-time logging)
                print("Could not attach SQL monitoring listeners")
    except Exception:
        # Don't fail app startup if monitoring cannot be initialized
        pass

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

    # Provide a flag to templates indicating whether this is the first-run (no users yet)
    @app.context_processor
    def inject_first_run_flag():
        try:
            from .models import User

            is_first_run = User.query.count() == 0
        except Exception:
            is_first_run = False
        return dict(is_first_run=is_first_run)


    # Avoid running the runtime DB creation/seeding when pytest is running
    import sys

    running_under_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST")) or any(
        "pytest" in str(a) for a in sys.argv
    )

    # Ensure the database schema exists at startup for normal runtimes.
    # If running under pytest, tests control DB lifecycle; otherwise, create
    # missing tables on first startup to avoid 500 errors when templates
    # attempt lightweight queries (e.g., business settings injector).
    if not running_under_pytest and not app.config.get("_SKIP_RUNTIME_SEEDING"):
        try:
            create_database(app)
            print("Ensured database schema exists at startup.")
        except Exception as e:
            # If schema creation fails, print and continue; downstream
            # requests may still experience errors but we avoid crashing app startup.
            print("Warning: could not create database schema at startup:", e)
    # Wrap the WSGI app to avoid noisy BrokenPipeError traces when clients
    # disconnect while the server is writing a response.
    try:
        from .wsgi_middleware import IgnoreBrokenPipeMiddleware

        app.wsgi_app = IgnoreBrokenPipeMiddleware(app.wsgi_app)
    except Exception:
        # If wrapping fails for any reason, continue returning the app
        # unwrapped. This should never happen in normal environments.
        pass

    # Optionally start a soft DB keepalive thread to avoid short-idle MySQL
    # connections being closed by the server (controlled by ENABLE_DB_KEEPALIVE)
    try:
        from .db_keepalive import start_keepalive

        # Default interval is 120s; configurable via DB_KEEPALIVE_INTERVAL
        try:
            interval = int(os.environ.get("DB_KEEPALIVE_INTERVAL", "120"))
        except Exception:
            interval = 120

        if os.environ.get("ENABLE_DB_KEEPALIVE", "1") != "0":
            try:
                start_keepalive(app, db, interval_seconds=interval)
            except Exception:
                print("Failed to start DB keepalive thread")
    except Exception:
        pass

    return app


def create_database(app):
    # Always ensure all tables exist (safe: create_all creates missing tables only)
    with app.app_context():
        db.create_all()

        # If the app requested skipping runtime seeding (set by create_app when
        # running under pytest), return early to avoid polluting test DBs.
        if app.config.get("_SKIP_RUNTIME_SEEDING"):
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

    # Do not auto-create a super-admin here. The application will allow
    # By default we do not auto-create a super-admin. However, for
    # automated deployments you may provide environment variables to
    # create a seeded Super Admin account on first-run. This is optional
    # and controlled by `DEFAULT_SUPERADMIN_EMAIL` and
    # `DEFAULT_SUPERADMIN_PASSWORD` or the `AUTO_CREATE_SUPERADMIN=1`
    # flag. Any seeded account will be forced to change password on
    # first login via `must_change_password=True`.
    try:
        from .models import User
        # Only create a seeded account when there are no users yet
        if User.query.count() == 0:
            default_email = os.environ.get("DEFAULT_SUPERADMIN_EMAIL")
            default_password = os.environ.get("DEFAULT_SUPERADMIN_PASSWORD")
            default_name = os.environ.get("DEFAULT_SUPERADMIN_NAME", "Super Admin")

            if default_email and default_password:
                try:
                    # Create the super admin with a forced password change
                    from werkzeug.security import generate_password_hash

                    new_user = User()
                    new_user.email = default_email
                    new_user.full_name = default_name
                    new_user.password = generate_password_hash(
                        default_password, method="pbkdf2:sha256"
                    )
                    new_user.role = "super_admin"
                    new_user.is_active = True
                    new_user.must_change_password = True
                    db.session.add(new_user)
                    db.session.commit()
                    print(
                        f"Created default Super Admin account: {default_email}. Password must be changed on first login."
                    )
                except Exception as e:
                    print("Warning: could not create default Super Admin:", e)
            elif os.environ.get("AUTO_CREATE_SUPERADMIN") == "1":
                # Create a seeded account with a generated temporary password
                try:
                    import secrets
                    from werkzeug.security import generate_password_hash

                    temp_pw = secrets.token_urlsafe(12)
                    email = os.environ.get("DEFAULT_SUPERADMIN_EMAIL", "admin@localhost")
                    name = os.environ.get("DEFAULT_SUPERADMIN_NAME", "Super Admin")

                    new_user = User()
                    new_user.email = email
                    new_user.full_name = name
                    new_user.password = generate_password_hash(temp_pw, method="pbkdf2:sha256")
                    new_user.role = "super_admin"
                    new_user.is_active = True
                    new_user.must_change_password = True
                    db.session.add(new_user)
                    db.session.commit()
                    print(
                        f"Created default Super Admin account: {email}. Temporary password: {temp_pw} — password must be changed on first login."
                    )
                except Exception as e:
                    print("Warning: could not auto-create Super Admin account:", e)
    except Exception:
        # Do not block startup if user seeding fails for any reason
        pass
