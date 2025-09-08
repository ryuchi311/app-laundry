from functools import wraps

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required

from . import db
from .models import BusinessSettings
from dotenv import load_dotenv, set_key, find_dotenv
from sqlalchemy import create_engine
import os

business_settings_bp = Blueprint("business_settings", __name__)


def super_admin_required(f):
    """Decorator to require super admin access"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            flash("Access denied. Super Admin privileges required.", "error")
            return redirect(url_for("views.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@business_settings_bp.route("/business-settings", methods=["GET", "POST"])
@login_required
@super_admin_required
def business_settings():
    """Business Settings Configuration Page"""
    settings = BusinessSettings.get_settings()

    if request.method == "POST":
        try:
            # Update business information
            settings.business_name = request.form.get("business_name", "").strip()
            settings.business_tagline = request.form.get("business_tagline", "").strip()
            settings.business_description = request.form.get(
                "business_description", ""
            ).strip()

            # Update contact information
            settings.phone = request.form.get("phone", "").strip()
            settings.email = request.form.get("email", "").strip()
            settings.address = request.form.get("address", "").strip()
            settings.operating_hours = request.form.get("operating_hours", "").strip()

            # Update footer information
            settings.footer_text = request.form.get("footer_text", "").strip()
            settings.copyright_text = request.form.get("copyright_text", "").strip()

            # Update social media links
            settings.facebook_url = request.form.get("facebook_url", "").strip()
            settings.instagram_url = request.form.get("instagram_url", "").strip()
            settings.website_url = request.form.get("website_url", "").strip()

            # Update system settings
            settings.currency_symbol = request.form.get("currency_symbol", "₱").strip()
            settings.timezone = request.form.get("timezone", "Asia/Manila").strip()

            # Advanced settings: Database URL and SMS (Semaphore)
            database_url = request.form.get("database_url", "").strip()
            semaphore_api_key = request.form.get("SEMAPHORE_API_KEY", "").strip()
            semaphore_sender = request.form.get("SEMAPHORE_SENDER_NAME", "").strip()

            # Persist environment values to .env (create if missing).
            try:
                # find existing .env in repo root or create a new .env
                dotenv_path = find_dotenv(usecwd=True)
                if not dotenv_path:
                    # create .env at repository root
                    dotenv_path = os.path.join(os.path.abspath(os.getcwd()), ".env")
                    # ensure file exists
                    open(dotenv_path, "a").close()

                # Validate and write DATABASE_URL only after a successful test connection
                if database_url:
                    try:
                        # Try a quick, short-lived test connection using SQLAlchemy
                        # Use pool_pre_ping to validate the server is reachable.
                        test_engine = create_engine(
                            database_url,
                            connect_args={"connect_timeout": 5},
                            pool_pre_ping=True,
                        )
                        conn = test_engine.connect()
                        conn.close()

                        # Check for presence of essential tables so we don't
                        # point the app to a DB missing the expected schema.
                        required_tables = {"user", "business_settings", "sms_settings"}
                        try:
                            inspector = __import__("sqlalchemy").inspect(test_engine)
                            existing = set(inspector.get_table_names())
                        except Exception:
                            # If inspector fails, fall back to assuming the DB
                            # is valid (we already checked connectability).
                            existing = set()

                        missing = required_tables - existing if existing else set()
                        if missing:
                            flash(
                                f"Database reachable but missing expected tables: {', '.join(sorted(missing))}. Database not saved.",
                                "error",
                            )
                            database_url = None

                        test_engine.dispose()
                    except Exception as e:
                        # Do not persist an invalid DATABASE_URL; inform the admin.
                        flash(
                            f"Database validation failed: {str(e)} — DATABASE_URL not saved.",
                            "error",
                        )
                        database_url = None

                # Write SMS values if provided
                if semaphore_api_key:
                    set_key(dotenv_path, "SEMAPHORE_API_KEY", semaphore_api_key)

                if semaphore_sender:
                    set_key(dotenv_path, "SEMAPHORE_SENDER_NAME", semaphore_sender)

                # If DB validated, persist and attempt a safe runtime rebind
                if database_url:
                    set_key(dotenv_path, "DATABASE_URL", database_url)
                    # reload into environment for current process (best-effort)
                    load_dotenv(dotenv_path, override=True)

                    # Try to reconfigure the Flask-SQLAlchemy engine at runtime so
                    # the app picks up the new DATABASE_URL without a full process
                    # restart. This is best-effort: if it fails, ask admin to restart.
                    try:
                        with current_app.app_context():
                            # Remove any session state and dispose the old engine
                            try:
                                db.session.remove()
                            except Exception:
                                pass

                            old_engine = None
                            try:
                                old_engine = db.get_engine(current_app)
                                try:
                                    old_engine.dispose()
                                except Exception:
                                    pass
                            except Exception:
                                # If we can't get the old engine, leave old_engine as None
                                old_engine = None

                            # Update app config so Flask-SQLAlchemy will create a new engine
                            current_app.config["SQLALCHEMY_DATABASE_URI"] = database_url
                            # Force creation of the new engine (best-effort)
                            try:
                                new_engine = db.get_engine(current_app)
                                # touch a connection to ensure it works
                                conn = new_engine.connect()
                                conn.close()
                            except Exception:
                                flash(
                                    "Database saved but runtime reconnect failed; please restart the service to apply the new DATABASE_URL.",
                                    "warning",
                                )
                            else:
                                flash("Database URL updated and reconnected successfully.", "success")
                    except Exception:
                        # If any part of the runtime rebind fails, notify admin but
                        # do not raise; require a manual restart as fallback.
                        flash(
                            "Database saved but runtime reconnect encountered an error; please restart the service to apply the new DATABASE_URL.",
                            "warning",
                        )
                else:
                    # reload phone/sms env changes even if DB wasn't changed
                    load_dotenv(dotenv_path, override=True)

            except Exception as e:
                # Non-fatal: save settings in DB and inform user
                flash(f"Warning: could not write to .env: {str(e)}", "warning")

            # Update metadata
            settings.updated_by = current_user.id

            db.session.commit()
            flash("Business settings updated successfully!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating business settings: {str(e)}", "error")

    return render_template("business_settings.html", settings=settings)


@business_settings_bp.route("/business-settings/preview", methods=["POST"])
@login_required
@super_admin_required
def preview_changes():
    """API endpoint to preview business settings changes"""
    try:
        data = request.get_json()

        return jsonify(
            {
                "success": True,
                "preview": {
                    "business_name": data.get("business_name", "ACCIO"),
                    "business_tagline": data.get(
                        "business_tagline", "Labhonon Laundry"
                    ),
                    "footer_text": data.get(
                        "footer_text", "Quality laundry services you can trust"
                    ),
                    "copyright_text": data.get(
                        "copyright_text",
                        "© 2025 ACCIO Labhonon Laundry. All rights reserved.",
                    ),
                },
            }
        )

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@business_settings_bp.route("/api/business-info")
@login_required
@super_admin_required
def get_business_info():
    """API endpoint to get current business information"""
    try:
        settings = BusinessSettings.get_settings()

        return jsonify(
            {
                "business_name": settings.business_name,
                "business_tagline": settings.business_tagline,
                "phone": settings.phone,
                "email": settings.email,
                "address": settings.address,
                "footer_text": settings.footer_text,
                "copyright_text": settings.copyright_text,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)})
