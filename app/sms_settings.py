from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .models import SMSSettings, SMSSettingsProfile
from .sms_service import send_sms_notification, sms_service

sms_settings_bp = Blueprint("sms_settings", __name__)


@sms_settings_bp.route("/sms-settings", methods=["GET", "POST"])
@login_required
def sms_settings():
    """SMS Settings Configuration Page"""
    settings = SMSSettings.get_settings()

    if request.method == "POST":
        try:
            form_keys = set(request.form.keys())
            updated = False

            # Define fields by group
            toggle_fields = {
                "received_enabled",
                "in_process_enabled",
                "ready_pickup_enabled",
                "completed_enabled",
                "welcome_enabled",
            }
            message_fields = {
                "received_message",
                "in_process_message",
                "ready_pickup_message",
                "completed_message",
                "welcome_message",
            }

            # Only update toggles if any toggle field is present in the POST (e.g., from the toggle form)
            if form_keys & toggle_fields:
                settings.received_enabled = "received_enabled" in form_keys
                settings.in_process_enabled = "in_process_enabled" in form_keys
                settings.ready_pickup_enabled = "ready_pickup_enabled" in form_keys
                settings.completed_enabled = "completed_enabled" in form_keys
                settings.welcome_enabled = "welcome_enabled" in form_keys
                updated = True

            # Only update messages if any message field is present in the POST (e.g., from the Save All form)
            if form_keys & message_fields:
                # Update each message only if present; ignore missing to avoid wiping values
                if "received_message" in form_keys:
                    settings.received_message = (
                        request.form.get("received_message") or ""
                    ).strip()
                if "in_process_message" in form_keys:
                    settings.in_process_message = (
                        request.form.get("in_process_message") or ""
                    ).strip()
                if "ready_pickup_message" in form_keys:
                    settings.ready_pickup_message = (
                        request.form.get("ready_pickup_message") or ""
                    ).strip()
                if "completed_message" in form_keys:
                    settings.completed_message = (
                        request.form.get("completed_message") or ""
                    ).strip()
                if "welcome_message" in form_keys:
                    settings.welcome_message = (
                        request.form.get("welcome_message") or ""
                    ).strip()
                updated = True

            # Commit only if something changed
            if updated:
                settings.updated_by = current_user.id
                db.session.commit()
                flash("SMS settings updated successfully!", "success")
            else:
                flash("No changes detected.", "info")

            # PRG for full message save; lightweight 204 for toggle auto-save
            if form_keys & message_fields:
                return redirect(url_for("sms_settings.sms_settings"))
            elif form_keys & toggle_fields:
                return ("", 204)

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating SMS settings: {str(e)}", "error")

    # Get SMS service configuration status
    sms_configured = sms_service.is_configured()

    # Get account status and credit balance
    account_info = (
        sms_service.get_account_status()
        if sms_configured
        else {
            "status": "Not Configured",
            "credit_balance": 0,
            "error": "SMS service not configured",
        }
    )

    # Load profiles
    profiles = SMSSettingsProfile.query.order_by(
        SMSSettingsProfile.is_default.desc(), SMSSettingsProfile.name.asc()
    ).all()

    # Find which profile matches current settings (by toggles/messages)
    active_profile = None
    for p in profiles:
        if (
            p.received_enabled == settings.received_enabled
            and p.in_process_enabled == settings.in_process_enabled
            and p.ready_pickup_enabled == settings.ready_pickup_enabled
            and p.completed_enabled == settings.completed_enabled
            and p.welcome_enabled == settings.welcome_enabled
            and p.received_message == settings.received_message
            and p.in_process_message == settings.in_process_message
            and p.ready_pickup_message == settings.ready_pickup_message
            and p.completed_message == settings.completed_message
            and p.welcome_message == settings.welcome_message
        ):
            active_profile = p
            break

    return render_template(
        "sms_settings.html",
        settings=settings,
        sms_configured=sms_configured,
        account_info=account_info,
        sender_name=sms_service.sender_name,
        sms_profiles=profiles,
        active_profile=active_profile,
    )


@sms_settings_bp.route("/sms-settings/profiles", methods=["GET"])
@login_required
def list_profiles():
    profiles = SMSSettingsProfile.query.order_by(
        SMSSettingsProfile.is_default.desc(), SMSSettingsProfile.name.asc()
    ).all()
    return jsonify(
        {
            "profiles": [
                {"id": p.id, "name": p.name, "is_default": p.is_default}
                for p in profiles
            ]
        }
    )


@sms_settings_bp.route("/sms-settings/profiles/<int:profile_id>", methods=["GET"])
@login_required
def get_profile(profile_id: int):
    """Return full profile settings for client-side loading (no side effects)."""
    p = SMSSettingsProfile.query.get_or_404(profile_id)
    return jsonify(
        {
            "success": True,
            "profile": {
                "id": p.id,
                "name": p.name,
                "is_default": p.is_default,
                "received_enabled": bool(p.received_enabled),
                "in_process_enabled": bool(p.in_process_enabled),
                "ready_pickup_enabled": bool(p.ready_pickup_enabled),
                "completed_enabled": bool(p.completed_enabled),
                "welcome_enabled": bool(p.welcome_enabled),
                "received_message": p.received_message or "",
                "in_process_message": p.in_process_message or "",
                "ready_pickup_message": p.ready_pickup_message or "",
                "completed_message": p.completed_message or "",
                "welcome_message": p.welcome_message or "",
            },
        }
    )


@sms_settings_bp.route("/sms-settings/profiles", methods=["POST"])
@login_required
def save_profile():
    name = (request.form.get("name") or "").strip()
    make_default = request.form.get("make_default") == "on"
    if not name:
        return jsonify({"success": False, "message": "Profile name is required"}), 400
    try:
        # If this is the first profile, force it to be default
        existing_count = SMSSettingsProfile.query.count()
        if existing_count == 0:
            make_default = True
        # Start from active settings, then override with any provided form values
        profile = SMSSettingsProfile.create_from_active(
            name, current_user.id, make_default
        )

        # Helper to parse checkbox truthy
        def as_bool(val: str | None) -> bool:
            return (val or "").lower() in ("on", "true", "1", "yes")

        # Optional: override toggles if provided (to capture latest UI state without needing a separate save)
        if "received_enabled" in request.form:
            profile.received_enabled = as_bool(request.form.get("received_enabled"))
        if "in_process_enabled" in request.form:
            profile.in_process_enabled = as_bool(request.form.get("in_process_enabled"))
        if "ready_pickup_enabled" in request.form:
            profile.ready_pickup_enabled = as_bool(
                request.form.get("ready_pickup_enabled")
            )
        if "completed_enabled" in request.form:
            profile.completed_enabled = as_bool(request.form.get("completed_enabled"))
        if "welcome_enabled" in request.form:
            profile.welcome_enabled = as_bool(request.form.get("welcome_enabled"))

        # Optional: override message templates if provided
        if "received_message" in request.form:
            profile.received_message = (
                request.form.get("received_message") or ""
            ).strip()
        if "in_process_message" in request.form:
            profile.in_process_message = (
                request.form.get("in_process_message") or ""
            ).strip()
        if "ready_pickup_message" in request.form:
            profile.ready_pickup_message = (
                request.form.get("ready_pickup_message") or ""
            ).strip()
        if "completed_message" in request.form:
            profile.completed_message = (
                request.form.get("completed_message") or ""
            ).strip()
        if "welcome_message" in request.form:
            profile.welcome_message = (
                request.form.get("welcome_message") or ""
            ).strip()
        db.session.commit()
        return jsonify(
            {
                "success": True,
                "id": profile.id,
                "name": profile.name,
                "is_default": profile.is_default,
            }
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@sms_settings_bp.route(
    "/sms-settings/profiles/<int:profile_id>/apply", methods=["POST"]
)
@login_required
def apply_profile(profile_id):
    profile = SMSSettingsProfile.query.get_or_404(profile_id)
    try:
        settings = profile.apply_to_active()
        settings.updated_by = current_user.id
        db.session.commit()
        flash(f"Applied profile '{profile.name}'", "success")
        return redirect(url_for("sms_settings.sms_settings"))
    except Exception as e:
        db.session.rollback()
        flash(f"Error applying profile: {str(e)}", "error")
        return redirect(url_for("sms_settings.sms_settings"))


@sms_settings_bp.route(
    "/sms-settings/profiles/<int:profile_id>/rename", methods=["POST"]
)
@login_required
def rename_profile(profile_id):
    profile = SMSSettingsProfile.query.get_or_404(profile_id)
    new_name = (request.form.get("name") or "").strip()
    if not new_name:
        return jsonify({"success": False, "message": "New name is required"}), 400
    try:
        profile.name = new_name
        profile.updated_by = current_user.id
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@sms_settings_bp.route(
    "/sms-settings/profiles/<int:profile_id>/default", methods=["POST"]
)
@login_required
def set_default_profile(profile_id):
    profile = SMSSettingsProfile.query.get_or_404(profile_id)
    try:
        profile.set_as_default()
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@sms_settings_bp.route(
    "/sms-settings/profiles/<int:profile_id>/delete", methods=["POST"]
)
@login_required
def delete_profile(profile_id):
    profile = SMSSettingsProfile.query.get_or_404(profile_id)
    try:
        if profile.is_default:
            return (
                jsonify(
                    {"success": False, "message": "Cannot delete the default profile"}
                ),
                400,
            )
        db.session.delete(profile)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


@sms_settings_bp.route("/sms-settings/account-info", methods=["GET"])
@login_required
def get_account_info():
    """API endpoint to get current account status and credit balance"""
    try:
        if not sms_service.is_configured():
            return jsonify({"success": False, "error": "SMS service not configured"})

        account_info = sms_service.get_account_status()
        return jsonify({"success": True, "account_info": account_info})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@sms_settings_bp.route("/sms-settings/test", methods=["POST"])
@login_required
def test_sms():
    """Test SMS functionality"""
    phone = request.form.get("test_phone", "").strip()
    message_type = request.form.get("message_type", "custom")
    custom_message = request.form.get("custom_message", "").strip()

    if not phone:
        return jsonify({"success": False, "message": "Phone number is required"})

    if not sms_service.is_configured():
        return jsonify({"success": False, "message": "SMS service is not configured"})

    try:
        settings = SMSSettings.get_settings()
        note = None

        # Generate test message based on type
        if message_type == "received":
            message = settings.format_message(
                settings.received_message,
                "John Doe",
                "TEST001",
                sms_service.sender_name,
                number_of_items=5,
            )
        elif message_type == "in_process":
            message = settings.format_message(
                settings.in_process_message,
                "John Doe",
                "TEST001",
                sms_service.sender_name,
                number_of_items=5,
            )
        elif message_type == "ready_pickup":
            message = settings.format_message(
                settings.ready_pickup_message,
                "John Doe",
                "TEST001",
                sms_service.sender_name,
                number_of_items=5,
            )
        elif message_type == "completed":
            message = settings.format_message(
                settings.completed_message,
                "John Doe",
                "TEST001",
                sms_service.sender_name,
                number_of_items=5,
            )
        elif message_type == "welcome":
            message = settings.format_message(
                settings.welcome_message, "John Doe", "", sms_service.sender_name
            )
        elif message_type == "custom":
            if not custom_message:
                return jsonify(
                    {"success": False, "message": "Custom message is required"}
                )
            message = custom_message
        else:
            return jsonify({"success": False, "message": "Invalid message type"})

        # Add an informational note if the selected type is disabled (tests still proceed)
        disabled_map = {
            "received": not settings.received_enabled,
            "in_process": not settings.in_process_enabled,
            "ready_pickup": not settings.ready_pickup_enabled,
            "completed": not settings.completed_enabled,
            "welcome": not settings.welcome_enabled,
        }
        if disabled_map.get(message_type):
            note = "Note: This notification type is disabled in settings. Test SMS sent anyway."

        # Send test SMS
        success = send_sms_notification(phone, message)

        if success:
            resp = {"success": True, "message": "Test SMS sent successfully!"}
            if note:
                resp["note"] = note
            return jsonify(resp)
        else:
            return jsonify({"success": False, "message": "Failed to send test SMS"})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error sending test SMS: {str(e)}"}
        )


@sms_settings_bp.route("/sms-settings/reset", methods=["POST"])
@login_required
def reset_messages():
    """Reset SMS messages to default"""
    try:
        settings = SMSSettings.get_settings()

        # Reset to default messages
        settings.received_message = "Hi {customer_name}! Your laundry (#{laundry_id}) has been received and is being processed. - {sender_name}"
        settings.in_process_message = "Hi {customer_name}! Your laundry (#{laundry_id}) is now being processed. We'll notify you when it's ready! - {sender_name}"
        settings.ready_pickup_message = "Hi {customer_name}! Great news! Your laundry (#{laundry_id}) is ready for pickup. Please visit us during business hours. - {sender_name}"
        settings.completed_message = "Hi {customer_name}! Your laundry (#{laundry_id}) has been completed. Thank you for choosing {sender_name}!"
        settings.welcome_message = "Welcome to {sender_name}, {customer_name}! We're excited to serve you. For inquiries, contact us at +639761111464."

        # Update metadata
        settings.updated_by = current_user.id

        db.session.commit()
        flash("SMS messages reset to default successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error resetting SMS messages: {str(e)}", "error")

    return redirect(url_for("sms_settings.sms_settings"))


@sms_settings_bp.route("/sms-settings/preview", methods=["POST"])
@login_required
def preview_message():
    """Preview formatted message"""
    try:
        message_template = request.form.get("message", "")
        settings = SMSSettings.get_settings()

        # Preview with sample data
        formatted_message = settings.format_message(
            message_template,
            "John Doe",
            "L001234",
            sms_service.sender_name,
            number_of_items=5,
        )

        return jsonify({"success": True, "preview": formatted_message})

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error previewing message: {str(e)}"}
        )


@sms_settings_bp.route("/sms-settings/bulk-message", methods=["GET", "POST"])
@login_required
def bulk_message():
    """Send bulk promotional/event messages to all customers"""
    from .models import BulkMessageHistory, Customer

    if request.method == "POST":
        message_text = request.form.get("message_text", "").strip()
        message_type = request.form.get("message_type", "promo")
        _send_to_all = request.form.get("send_to_all") == "on"

        if not message_text:
            flash("Message text is required", "error")
            return redirect(url_for("sms_settings.bulk_message"))

        if not sms_service.is_configured():
            flash(
                "SMS service is not configured. Please set up your API credentials first.",
                "error",
            )
            return redirect(url_for("sms_settings.bulk_message"))

        # Get all active customers with phone numbers
        customers = Customer.query.filter(
            Customer.phone.isnot(None), Customer.is_active
        ).all()
        customers_with_phones = [c for c in customers if c.phone and c.phone.strip()]

        if not customers_with_phones:
            flash("No customers found with phone numbers", "warning")
            return redirect(url_for("sms_settings.bulk_message"))

        # Create bulk message history record
        bulk_history = BulkMessageHistory()
        bulk_history.message_text = message_text
        bulk_history.message_type = message_type
        bulk_history.sent_by_user_id = current_user.id
        bulk_history.total_recipients = len(customers_with_phones)
        db.session.add(bulk_history)

        success_count = 0
        failed_count = 0

        for customer in customers_with_phones:
            try:
                # Format message with customer name and sender name
                formatted_message = message_text.replace(
                    "{customer_name}", customer.full_name
                )
                formatted_message = formatted_message.replace(
                    "{sender_name}", sms_service.sender_name
                )

                if sms_service.send_sms(customer.phone, formatted_message):
                    success_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                print(f"Error sending SMS to {customer.full_name}: {str(e)}")

        # Update bulk message history with results
        bulk_history.successful_sends = success_count
        bulk_history.failed_sends = failed_count
        db.session.commit()

        if success_count > 0:
            flash(
                f"Bulk message sent successfully to {success_count} customers!",
                "success",
            )
        if failed_count > 0:
            flash(f"Failed to send message to {failed_count} customers", "warning")

        return redirect(url_for("sms_settings.bulk_message"))

    # GET request - show the form
    from .models import BulkMessageHistory, Customer

    total_customers = Customer.query.filter(Customer.is_active).count()
    customers_with_phones = Customer.query.filter(
    Customer.phone.isnot(None), Customer.is_active
    ).count()

    # Check if SMS service is configured
    sms_configured = sms_service.is_configured()

    # Get recent bulk message history
    recent_campaigns = (
        BulkMessageHistory.query.order_by(BulkMessageHistory.sent_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "bulk_message.html",
        total_customers=total_customers,
        customers_with_phones=customers_with_phones,
        recent_campaigns=recent_campaigns,
        sms_configured=sms_configured,
    )


@sms_settings_bp.route("/sms-settings/customer-list")
@login_required
def customer_list():
    """Get list of active customers for bulk messaging preview"""
    from .models import Customer

    customers = Customer.query.filter(
    Customer.phone.isnot(None), Customer.is_active
    ).all()
    customer_data = []

    for customer in customers:
        if customer.phone and customer.phone.strip():
            customer_data.append(
                {
                    "id": customer.id,
                    "name": customer.full_name,
                    "phone": customer.phone,
                    "email": customer.email or "N/A",
                }
            )

    return jsonify({"customers": customer_data})


@sms_settings_bp.route("/sms-settings/preview-bulk", methods=["POST"])
@login_required
def preview_bulk_message():
    """Preview how bulk message will look"""
    message_text = request.form.get("message_text", "")
    customer_name = request.form.get("sample_customer_name", "John Doe")

    if not message_text:
        return jsonify({"success": False, "message": "Message text is required"})

    try:
        # Format message with sample data
        formatted_message = message_text.replace("{customer_name}", customer_name)
        formatted_message = formatted_message.replace(
            "{sender_name}", sms_service.sender_name
        )

        return jsonify(
            {
                "success": True,
                "preview": formatted_message,
                "length": len(formatted_message),
            }
        )

    except Exception as e:
        return jsonify(
            {"success": False, "message": f"Error previewing message: {str(e)}"}
        )
