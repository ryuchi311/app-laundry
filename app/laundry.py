import random
import string
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_mail import Message
from sqlalchemy import func, or_  # type: ignore

from . import db, mail
from .models import (
    Customer,
    Laundry,
    LaundryAuditLog,
    LaundryStatusHistory,
    Service,
    User,
)
from .sms_service import send_laundry_status_sms, send_sms_notification
import base64
import io

laundry = Blueprint("laundry", __name__)


def log_laundry_change(
    laundry_id, action, field_changed=None, old_value=None, new_value=None
):
    """Log laundry changes for audit trail"""
    try:
        audit_log = LaundryAuditLog()
        audit_log.laundry_id = laundry_id
        audit_log.action = action
        audit_log.field_changed = field_changed
        audit_log.old_value = str(old_value) if old_value is not None else None
        audit_log.new_value = str(new_value) if new_value is not None else None
        audit_log.changed_by = current_user.id
        audit_log.ip_address = request.remote_addr

        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")


def generate_laundry_id():
    """Generate a unique 10-digit Laundry ID"""
    while True:
        laundry_id = "".join(random.choices(string.digits, k=10))
        if not Laundry.query.filter_by(laundry_id=laundry_id).first():
            return laundry_id


def send_notification_email(customer_email, subject, body):
    """Send email notification to customer"""
    try:
        msg = Message(
            subject, sender="noreply@acciolaundry.com", recipients=[customer_email]
        )
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_notification(customer, subject, email_body, sms_message=None):
    """Send both email and SMS notifications to customer"""
    email_sent = False
    sms_sent = False

    # Send email if customer has email
    if customer.email:
        email_sent = send_notification_email(customer.email, subject, email_body)

    # Send SMS if customer has phone and SMS message is provided
    if customer.phone and sms_message:
        sms_sent = send_sms_notification(customer.phone, sms_message)

    return email_sent or sms_sent


@laundry.route("/list")
@login_required
def list_laundries():
    # Server-side pagination and filtering
    status_param = (request.args.get("status") or "").strip().lower()
    date_param = (request.args.get("date") or "").strip()
    # Search query (q or search)
    search_q = (request.args.get("q") or request.args.get("search") or "").strip()
    # Pagination params
    try:
        page = int(request.args.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", 12))
    except (ValueError, TypeError):
        per_page = 12
    status_map = {
        "received": "Received",
        "inprocess": "Received",
        "in-progress": "Received",
        "in_progress": "Received",
        "in process": "Received",
        "ready": "Ready for Pickup",
        "pickup": "Ready for Pickup",
        "readyforpickup": "Ready for Pickup",
        "ready-for-pickup": "Ready for Pickup",
        "ready_for_pickup": "Ready for Pickup",
        "completed": "Completed",
        "pickedup": "Picked Up",
        "picked-up": "Picked Up",
        "picked up": "Picked Up",
    }
    selected_status = status_map.get(status_param)

    # Optional filter by customer_id (used when linking from customer directory)
    customer_id_param = request.args.get("customer_id")
    base_query = Laundry.query
    customer_obj = None
    if customer_id_param:
        try:
            cid = int(customer_id_param)
            base_query = base_query.filter(Laundry.customer_id == cid)
            customer_obj = Customer.query.get(cid)
        except Exception:
            # ignore invalid ids
            customer_obj = None
    if selected_status:
        base_query = base_query.filter(Laundry.status == selected_status)
    if date_param:
        try:
            date_obj = datetime.strptime(date_param, "%Y-%m-%d").date()
            base_query = base_query.filter(func.date(Laundry.date_received) == date_obj)
        except Exception:
            pass
    # Apply search filter across laundry id, customer name, and phone
    if search_q:
        like = f"%{search_q}%"
        # join with Customer for name/phone searches
        base_query = base_query.join(Customer).filter(
            db.or_(
                Laundry.laundry_id.ilike(like),
                Customer.full_name.ilike(like),
                Customer.phone.ilike(like),
                Laundry.status.ilike(like),
            )
        )

    base_query = base_query.order_by(Laundry.date_received.desc())

    # Paginate to limit load and avoid long scrolling
    laundries_page = base_query.paginate(page=page, per_page=per_page, error_out=False)
    laundries = laundries_page.items
    total_count = laundries_page.total

    # If this is an AJAX fragment request, return partial HTML for cards and pagination
    if request.args.get('ajax') == '1':
        from flask import render_template as rt
        view_type = request.args.get('view', 'cards')
        pagination_html = rt('laundries/_pagination_fragment.html', laundries=laundries, laundries_page=laundries_page, total_count=total_count, per_page=per_page)
        if view_type == 'table':
            fragment = rt('laundries/_table_fragment.html', laundries=laundries)
        elif view_type == 'list':
            fragment = rt('laundries/_list_fragment.html', laundries=laundries)
        else:
            fragment = rt('laundries/_cards_fragment.html', laundries=laundries)
        return jsonify({'fragment': fragment, 'pagination': pagination_html, 'view': view_type})

    # Device detection for view type
    user_agent = request.user_agent.string.lower()
    if "ipad" in user_agent or "tablet" in user_agent:
        default_view = "list"
    elif "mobile" in user_agent or "android" in user_agent or "iphone" in user_agent:
        default_view = "cards"
    else:
        default_view = "table"

    return render_template(
        "laundries/laundry_list.html",
        user=current_user,
        laundries=laundries,
        laundries_page=laundries_page,
        total_count=total_count,
        selected_status=status_param,
        customer=customer_obj,
        default_view=default_view,
        search_q=search_q,
        per_page=per_page,
    )
    


@laundry.route("/search-customers")
@login_required
def search_customers():
    """Lightweight typeahead search for customers by name/phone/email."""
    q = (request.args.get("q") or "").strip()
    limit = 10
    if not q:
        return jsonify({"results": []})

    # Split numeric vs text to improve phone searches
    like = f"%{q}%"

    query = Customer.query
    # Build filters safely (avoid injecting False into or_)
    filters = [Customer.full_name.ilike(like), Customer.email.ilike(like)]
    if hasattr(Customer, "phone"):
        filters.append(Customer.phone.ilike(like))
    query = query.filter(or_(*filters))

    results = query.order_by(Customer.full_name.asc()).limit(limit).all()
    payload = []
    for c in results:
        payload.append(
            {
                "id": c.id,
                "name": getattr(c, "full_name", "Unknown"),
                "phone": getattr(c, "phone", "") or "",
                "email": getattr(c, "email", "") or "",
            }
        )

    return jsonify({"results": payload})


@laundry.route("/add-multiple", methods=["GET", "POST"])
@login_required
def add_multiple_laundry():
    """Add multiple laundry loads for one customer at once"""
    if request.method == "POST":
        # Debug: Print all form data
        print("=== FORM DATA RECEIVED ===")
        for key, value in request.form.items():
            print(f"{key}: {value}")
        print("=" * 30)
        
        customer_id = request.form.get("customerId")
        
        # Validate customer
        try:
            customer_pk = int(customer_id) if customer_id is not None else None
        except (ValueError, TypeError):
            customer_pk = None
        customer = Customer.query.get(customer_pk)
        if not customer:
            flash("Customer not found!", category="error")
            return redirect(url_for("laundry.add_multiple_laundry"))
        
        # Get all load data from form
        load_count = 0
        created_laundries = []
        
        # Process each load (load_1, load_2, load_3, etc.)
        for i in range(1, 21):  # Support up to 20 loads
            service_id = request.form.get(f"serviceType_{i}")
            if not service_id:
                continue
                
            item_count = request.form.get(f"itemCount_{i}")
            weight_kg = request.form.get(f"weight_kg_{i}")
            notes = request.form.get(f"notes_{i}")
            
            # Get service details
            try:
                service_pk = int(service_id) if service_id is not None else None
            except (ValueError, TypeError):
                continue
            service = Service.query.get(service_pk)
            if not service:
                continue
            
            # Validate weight_kg - handle None case
            weight_value = 0.0
            if weight_kg:
                try:
                    weight_value = float(weight_kg)
                except (ValueError, TypeError):
                    weight_value = 0.0
            
            # Create laundry entry
            new_laundry = Laundry()
            new_laundry.laundry_id = generate_laundry_id()
            new_laundry.customer_id = customer_pk
            try:
                new_laundry.item_count = int(item_count) if item_count is not None else 0
            except (ValueError, TypeError):
                new_laundry.item_count = 0
            new_laundry.service_id = service_pk
            new_laundry.service = service
            new_laundry.service_type = service.name
            new_laundry.weight_kg = weight_value
            new_laundry.notes = notes
            new_laundry.status = "Received"
            
            # Calculate and set the price
            new_laundry.update_price()
            
            db.session.add(new_laundry)
            created_laundries.append(new_laundry)
            load_count += 1
        
        if load_count == 0:
            flash("No valid loads were submitted!", category="error")
            return redirect(url_for("laundry.add_multiple_laundry"))
        
        # Commit all laundries at once
        db.session.commit()
        
        # Log and create notifications for all created laundries
        for new_laundry in created_laundries:
            # Log the Laundry creation
            log_laundry_change(new_laundry.laundry_id, "CREATED")
            
            # Log initial status in status history
            LaundryStatusHistory.log_status_change(
                laundry_id=new_laundry.laundry_id,
                old_status=None,
                new_status="Received",
                changed_by=current_user.id,
                notes=f"Initial laundry created by {current_user.full_name} (Multi-load batch)",
            )
            
            # Create notification for new laundry order
            try:
                from .notifications import create_laundry_notification
                create_laundry_notification(
                    user_id=current_user.id, laundry=new_laundry, message_type="new_order"
                )
            except Exception as e:
                print(f"Failed to create notification: {e}")
            
            # Send SMS for initial status (Received)
            try:
                send_laundry_status_sms(new_laundry.customer, new_laundry, "Received")
            except Exception as e:
                print(f"Failed to send 'Received' SMS: {e}")
        
        db.session.commit()
        
        flash(f"Successfully created {load_count} laundry load(s) for {customer.full_name}!", category="success")
        return redirect(url_for("laundry.list_laundries"))
    
    customers = Customer.query.all()
    services = Service.query.filter_by(is_active=True).all()
    
    # Convert services to dictionary for JSON serialization
    services_data = [
        {
            'id': s.id,
            'name': s.name,
            'base_price': float(s.base_price),
            'price_per_kg': float(s.price_per_kg),
            'estimated_hours': s.estimated_hours,
            'is_active': s.is_active
        }
        for s in services
    ]
    
    return render_template(
        "laundries/laundry_add_multiple.html",
        user=current_user,
        customers=customers,
        services=services,
        services_json=services_data,
    )


@laundry.route("/add", methods=["GET", "POST"])
@login_required
def add_laundry():
    if request.method == "POST":
        customer_id = request.form.get("customerId")
        item_count = request.form.get("itemCount")
        service_type = request.form.get("serviceType")  # This now contains service_id
        weight_kg = request.form.get("weight_kg")
        notes = request.form.get("notes")

        # Validate customer
        try:
            customer_pk = int(customer_id) if customer_id is not None else None
        except (ValueError, TypeError):
            customer_pk = None
        customer = Customer.query.get(customer_pk)
        if not customer:
            flash("Customer not found!", category="error")
            return redirect(url_for("laundry.add_laundry"))

        # Get service details
        try:
            service_pk = int(service_type) if service_type is not None else None
        except (ValueError, TypeError):
            service_pk = None
        service = Service.query.get(service_pk)
        if not service:
            flash("Service not found!", category="error")
            return redirect(url_for("laundry.add_laundry"))

        # Validate weight_kg - handle None case
        weight_value = 0.0
        if weight_kg:
            try:
                weight_value = float(weight_kg)
            except (ValueError, TypeError):
                weight_value = 0.0

        new_laundry = Laundry()
        new_laundry.laundry_id = generate_laundry_id()
        new_laundry.customer_id = customer_pk
        # Ensure numeric types
        try:
            new_laundry.item_count = int(item_count) if item_count is not None else 0
        except (ValueError, TypeError):
            new_laundry.item_count = 0
        new_laundry.service_id = service_pk  # Store service_id
        # Attach relationship for immediate pricing
        new_laundry.service = service
        new_laundry.service_type = (
            service.name
        )  # Store service name for backward compatibility
        new_laundry.weight_kg = weight_value
        new_laundry.notes = notes
        new_laundry.status = "Received"

        # Calculate and set the price
        new_laundry.update_price()

        db.session.add(new_laundry)
        db.session.commit()

        # Log the Laundry creation
        log_laundry_change(new_laundry.laundry_id, "CREATED")

        # Log initial status in status history
        LaundryStatusHistory.log_status_change(
            laundry_id=new_laundry.laundry_id,
            old_status=None,
            new_status="Received",
            changed_by=current_user.id,
            notes=f"Initial laundry created by {current_user.full_name}",
        )

        # Create notification for new laundry order
        try:
            from .notifications import create_laundry_notification

            create_laundry_notification(
                user_id=current_user.id, laundry=new_laundry, message_type="new_order"
            )
        except Exception as e:
            print(f"Failed to create notification: {e}")

        db.session.commit()

        # Send SMS for initial status (Received) using template and toggles
        try:
            send_laundry_status_sms(new_laundry.customer, new_laundry, "Received")
        except Exception as e:
            print(f"Failed to send 'Received' SMS: {e}")

        flash("Laundry created!", category="success")
        # Redirect to edit page for review before printing
        return redirect(
            url_for("laundry.edit_laundry", laundry_id=new_laundry.laundry_id)
        )

    customers = Customer.query.all()
    services = Service.query.filter_by(is_active=True).all()
    return render_template(
        "laundries/laundry_add.html",
        user=current_user,
        customers=customers,
        services=services,
    )


@laundry.route("/receipt/<laundry_id>")
@login_required
def print_receipt(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    # Generate QR code PNG (base64) if qrcode module available
    qr_base64 = None
    try:
        # Lazy import to avoid editor static import warnings when package isn't installed yet
        try:
            import qrcode as _qrcode  # type: ignore
        except Exception:
            _qrcode = None

        if _qrcode:
            qr_payload = f"/laundry/receipt/{laundry_item.laundry_id}"
            qr = _qrcode.QRCode(border=1)
            qr.add_data(qr_payload)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            qr_base64 = base64.b64encode(buf.read()).decode("ascii")
    except Exception as e:
        print(f"Failed to generate QR code: {e}")

    return render_template(
        "laundries/laundry_receipt.html",
        laundry=laundry_item,
        qr_base64=qr_base64,
    )


@laundry.route("/edit/<laundry_id>", methods=["GET", "POST"])
@login_required
def edit_laundry(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()

    if request.method == "POST":
    # Store original values for audit logging (kept inline where used below)

        # Update Laundry fields
        new_item_count = request.form.get("itemCount")
        new_service_type = request.form.get(
            "serviceType"
        )  # This now contains service_id
        new_weight_kg = request.form.get("weight_kg")
        new_notes = request.form.get("notes")
        new_customer_id = request.form.get("customerId")

        # Get service details
        service = Service.query.get(new_service_type)
        if not service:
            flash("Service not found!", category="error")
            return redirect(url_for("laundry.edit_laundry", laundry_id=laundry_id))

        # Track changes and log them
        changes_made = False

        # Validate and convert form values with null checks
        try:
            new_service_id = int(new_service_type) if new_service_type else 0
        except (ValueError, TypeError):
            new_service_id = 0

        try:
            new_weight_value = float(new_weight_kg) if new_weight_kg else 0.0
        except (ValueError, TypeError):
            new_weight_value = 0.0

        if str(laundry_item.item_count) != new_item_count:
            log_laundry_change(
                laundry_item.laundry_id,
                "EDITED",
                "item_count",
                laundry_item.item_count,
                new_item_count,
            )
            laundry_item.item_count = new_item_count
            changes_made = True

        if laundry_item.service_id != new_service_id:
            log_laundry_change(
                laundry_item.laundry_id,
                "EDITED",
                "service",
                (
                    laundry_item.service.name
                    if laundry_item.service
                    else laundry_item.service_type
                ),
                service.name,
            )
            laundry_item.service_id = new_service_id
            # Keep relationship in sync for pricing
            laundry_item.service = service
            laundry_item.service_type = (
                service.name
            )  # Update for backward compatibility
            changes_made = True

        if laundry_item.weight_kg != new_weight_value:
            log_laundry_change(
                laundry_item.laundry_id,
                "EDITED",
                "weight_kg",
                laundry_item.weight_kg,
                new_weight_kg,
            )
            laundry_item.weight_kg = new_weight_value
            changes_made = True

        if laundry_item.notes != new_notes:
            log_laundry_change(
                laundry_item.laundry_id,
                "EDITED",
                "notes",
                laundry_item.notes or "None",
                new_notes or "None",
            )
            laundry_item.notes = new_notes
            changes_made = True

        # Update customer if changed
        if new_customer_id and int(new_customer_id) != laundry_item.customer_id:
            customer = Customer.query.get(new_customer_id)
            if customer:
                old_customer = Customer.query.get(laundry_item.customer_id)
                log_laundry_change(
                    laundry_item.laundry_id,
                    "EDITED",
                    "customer",
                    old_customer.full_name if old_customer else "Unknown",
                    customer.full_name,
                )
                laundry_item.customer_id = new_customer_id
                changes_made = True

        # Update tracking fields if changes were made
        if changes_made:
            laundry_item.last_edited_by = current_user.id
            laundry_item.last_edited_at = datetime.utcnow()
            laundry_item.edit_count = (laundry_item.edit_count or 0) + 1
            laundry_item.is_modified = True

            # Recalculate price if item count, service type, or weight changed
            laundry_item.update_price()

        db.session.commit()
        flash("Laundry updated successfully!", category="success")

        # Create a notification for the edit
        try:
            from .notifications import create_laundry_notification

            create_laundry_notification(
                user_id=current_user.id, laundry=laundry_item, message_type="edited"
            )
        except Exception as e:
            print(f"Failed to create edit notification: {e}")

        # Check if user wants to print after editing
        if request.form.get("action") == "save_and_print":
            return redirect(
                url_for("laundry.print_receipt", laundry_id=laundry_item.laundry_id)
            )
        else:
            return redirect(url_for("laundry.list_laundries"))

    customers = Customer.query.all()
    services = Service.query.filter_by(is_active=True).all()
    return render_template(
        "laundries/laundry_edit.html",
        user=current_user,
        laundry=laundry_item,
        customers=customers,
        services=services,
    )


@laundry.route("/update-status/<laundry_id>", methods=["POST"])
@login_required
def update_status(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    new_status = request.form.get("status")

    if new_status not in ["Received", "Ready for Pickup", "Completed"]:
        flash("Invalid status!", category="error")
        return redirect(url_for("laundry.list_laundries"))

    # Log status change if status actually changed
    if laundry_item.status != new_status:
        old_status = laundry_item.status

        # Log in audit log (legacy)
        log_laundry_change(
            laundry_item.laundry_id, "STATUS_CHANGED", "status", old_status, new_status
        )

        # Log in status history (new detailed tracking)
        LaundryStatusHistory.log_status_change(
            laundry_id=laundry_item.laundry_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
            notes=f"Status changed by {current_user.full_name}",
        )

        # Update the laundry status
        laundry_item.status = new_status
        laundry_item.last_edited_by = current_user.id
        laundry_item.last_edited_at = datetime.utcnow()
        laundry_item.edit_count = (laundry_item.edit_count or 0) + 1
        laundry_item.is_modified = True

        db.session.commit()

        # Create notification for status change
        try:
            from .notifications import create_laundry_notification

            if new_status == "Ready for Pickup":
                create_laundry_notification(
                    user_id=current_user.id,
                    laundry=laundry_item,
                    message_type="ready_pickup",
                )
            elif new_status == "Completed":
                create_laundry_notification(
                    user_id=current_user.id,
                    laundry=laundry_item,
                    message_type="completed",
                )
            else:
                create_laundry_notification(
                    user_id=current_user.id,
                    laundry=laundry_item,
                    message_type="status_update",
                )
        except Exception as e:
            print(f"Failed to create notification: {e}")

        # Send email notification based on status (SMS handled via templates/toggles below)
        if new_status == "Ready for Pickup":
            send_notification(
                laundry_item.customer,
                "Pickup ready!",
                f"Your laundry (Laundry #{laundry_item.laundry_id}) is ready for pickup at our location.",
                sms_message=None,
            )
        elif new_status == "Completed":
            send_notification(
                laundry_item.customer,
                "Laundry Completed!",
                f"Your laundry (Laundry #{laundry_item.laundry_id}) has been completed. Thank you for choosing ACCIO Laundry!",
                sms_message=None,
            )
    elif new_status == "Received":
        send_notification(
            laundry_item.customer,
            "Laundry Received",
            f"Your laundry (Laundry #{laundry_item.laundry_id}) is now being processed. We'll notify you when it's ready!",
            sms_message=None,
        )

    # Send SMS using template-driven function (respects toggles and placeholders)
    try:
        send_laundry_status_sms(laundry_item.customer, laundry_item, new_status)
    except Exception as e:
        print(f"Failed to send status '{new_status}' SMS: {e}")

    # Award loyalty points when order is completed
    if new_status == "Completed":
        # Award loyalty points when order is completed
        from .models import CustomerLoyalty, LoyaltyProgram, LoyaltyTransaction

        program = LoyaltyProgram.query.filter_by(is_active=True).first()
        if program:
            try:
                # Calculate points based on total amount (use price field)
                # Use rounding per-order to avoid cumulative truncation loss
                points_earned = int(
                    round((laundry_item.price or 0) * (program.points_per_peso or 1.0))
                )

                # Get or create customer loyalty record
                loyalty = CustomerLoyalty.query.filter_by(
                    customer_id=laundry_item.customer_id, program_id=program.id
                ).first()
                if not loyalty:
                    loyalty = CustomerLoyalty()
                    loyalty.customer_id = laundry_item.customer_id
                    loyalty.program_id = program.id
                    loyalty.points_balance = 0
                    loyalty.total_points_earned = 0
                    loyalty.total_points_redeemed = 0
                    db.session.add(loyalty)

                # Award points
                loyalty.points_balance += points_earned
                loyalty.total_points_earned += points_earned

                # Create transaction record
                transaction = LoyaltyTransaction()
                transaction.customer_id = laundry_item.customer_id
                transaction.program_id = program.id
                transaction.laundry_id = laundry_item.laundry_id
                transaction.transaction_type = "earned"
                transaction.points = points_earned
                transaction.description = (
                    f"Points earned from laundry order #{laundry_item.laundry_id}"
                )

                db.session.add(transaction)

                db.session.commit()
                flash(
                    f"Customer earned {points_earned} loyalty points!", category="info"
                )

            except Exception as e:
                print(f"Error awarding loyalty points: {e}")
                db.session.rollback()

    flash(f'Laundry status updated to "{new_status}"!', category="success")

    return redirect(url_for("laundry.list_laundries"))


@laundry.route("/status-history/<laundry_id>")
@login_required
def view_status_history(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    status_history = (
        LaundryStatusHistory.query.filter_by(laundry_id=laundry_id)
        .order_by(LaundryStatusHistory.changed_at.desc())
        .all()
    )

    return render_template(
        "laundries/laundry_status_history.html",
        user=current_user,
        laundry=laundry_item,
        status_history=status_history,
    )


@laundry.route("/audit/<laundry_id>")
@login_required
def view_audit_log(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    audit_logs = (
        LaundryAuditLog.query.filter_by(laundry_id=laundry_id)
        .order_by(LaundryAuditLog.changed_at.desc())
        .all()
    )

    # Process audit logs to group by action and add user info
    processed_logs = []
    for log in audit_logs:
        user = User.query.get(log.changed_by)
        processed_logs.append(
            {
                "id": log.id,
                "action": log.action,
                "field_changed": log.field_changed,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "timestamp": log.changed_at,
                "user_email": user.email if user else "Unknown User",
                "ip_address": log.ip_address,
            }
        )

    return render_template(
        "laundries/laundry_audit.html",
        user=current_user,
        laundry=laundry_item,
        audit_logs=processed_logs,
    )


@laundry.route("/delete/<laundry_id>", methods=["POST"])
@login_required
def delete_laundry(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    # Only administrators may delete laundries
    if not (current_user.is_admin() or current_user.is_super_admin()):
        # Audit the forbidden attempt
        try:
            log_laundry_change(
                laundry_item.laundry_id,
                "DELETE_FORBIDDEN",
                "delete_attempt",
                f"by_user:{current_user.id}",
                "forbidden",
            )
        except Exception:
            pass

        # If AJAX, return JSON 403
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'forbidden'}), 403

        flash("Only administrators can delete laundries.", category="error")
        return redirect(url_for("laundry.list_laundries"))

    # Log the deletion
    log_laundry_change(
        laundry_item.laundry_id, "DELETED", "Laundry", f"Laundry {laundry_id}", "Deleted"
    )

    # Delete associated records first (foreign key constraints)
    # Create deletion notification before removing records
    try:
        from .notifications import create_laundry_notification

        create_laundry_notification(
            user_id=current_user.id, laundry=laundry_item, message_type="deleted"
        )
    except Exception as e:
        print(f"Failed to create deletion notification: {e}")

    LaundryStatusHistory.query.filter_by(laundry_id=laundry_id).delete()
    LaundryAuditLog.query.filter_by(laundry_id=laundry_id).delete()

    # Delete the Laundry
    db.session.delete(laundry_item)
    db.session.commit()

    flash("Laundry deleted successfully!", category="success")
    return redirect(url_for("laundry.list_laundries"))
