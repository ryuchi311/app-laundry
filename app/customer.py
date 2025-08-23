from flask import (
    Blueprint,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

import csv
import io
import re

from . import db
from .decorators import user_or_admin_required
from .models import Customer, Laundry
from .sms_service import send_welcome_sms


customer = Blueprint("customer", __name__)


@customer.route("/view/<int:id>")
@user_or_admin_required
def view_customer(id):
    customer_obj = Customer.query.get_or_404(id)
    # Paginated laundries for this customer (server-side pagination)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    # Initialize defaults so variables exist regardless of paginate outcome
    total_earned = 0.0
    loyalty = None
    total_points_today = 0
    total_points_redeemed = 0
    try:
        laundries_page = (
            Laundry.query.filter_by(customer_id=customer_obj.id)
            .order_by(Laundry.date_received.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        laundries = laundries_page.items
        total_laundries = laundries_page.total
    except Exception:
        # Fallback to small in-memory list if something goes wrong
        try:
            laundries = (
                Laundry.query.filter_by(customer_id=customer_obj.id)
                .order_by(Laundry.date_received.desc())
                .limit(6)
                .all()
            )
            total_laundries = Laundry.query.filter_by(
                customer_id=customer_obj.id
            ).count()
            laundries_page = type(
                "P",
                (),
                {
                    "items": laundries,
                    "page": 1,
                    "per_page": len(laundries),
                    "pages": 1,
                    "total": total_laundries,
                },
            )()
        except Exception:
            laundries = []
            total_laundries = 0
            laundries_page = type(
                "P",
                (),
                {
                    "items": laundries,
                    "page": 1,
                    "per_page": per_page,
                    "pages": 0,
                    "total": 0,
                },
            )()
        # Loyalty info (may create record if missing) - fetch early so totals use loyalty summary when present
        try:
            loyalty = customer_obj.get_loyalty_info()
        except Exception:
            loyalty = None
    # Compute totals and loyalty metrics (always run)
    try:
        # Compute total points earned for this customer (use loyalty summary when available).
        from sqlalchemy import func
        from .models import LoyaltyTransaction, CustomerLoyalty

        if loyalty:
            # Use the loyalty summary field which is maintained when points are awarded.
            total_earned = int(getattr(loyalty, "total_points_earned", 0) or 0)
        else:
            # Fallback: sum point transactions for this customer's loyalty records (case-insensitive).
            total = (
                db.session.query(func.coalesce(func.sum(LoyaltyTransaction.points), 0))
                .join(CustomerLoyalty, LoyaltyTransaction.customer_loyalty_id == CustomerLoyalty.id)
                .filter(CustomerLoyalty.customer_id == customer_obj.id)
                .filter(func.lower(LoyaltyTransaction.transaction_type) == "earned")
                .scalar()
                or 0
            )
            total_earned = int(total)
    except Exception:
        total_earned = 0

    try:
        if loyalty:
            from datetime import date as _date

            from sqlalchemy import func

            from .models import LoyaltyTransaction

            # Points earned today (transaction_type == 'EARNED')
            today = _date.today()
            pts = (
                db.session.query(func.coalesce(func.sum(LoyaltyTransaction.points), 0))
                .filter(
                    LoyaltyTransaction.customer_loyalty_id == loyalty.id,
                    func.date(LoyaltyTransaction.created_at) == today,
                    func.lower(LoyaltyTransaction.transaction_type) == "earned",
                )
                .scalar()
                or 0
            )
            total_points_today = int(pts)

            # Total points redeemed (use the loyalty summary field)
            total_points_redeemed = int(loyalty.total_points_redeemed or 0)
    except Exception:
        total_points_today = 0
        total_points_redeemed = int(getattr(loyalty, "total_points_redeemed", 0) or 0)

    # Permission: decide whether the current user can view points for this customer.
    # Rule: admins and managers can see points; a user whose email matches the customer's email can also see their own points.
    try:
        show_points = False
        if current_user.is_authenticated:
            # Allow admins, managers, and basic users to view points.
            # Also allow a user to view their own points when email matches the customer record.
            if (
                getattr(current_user, "is_admin", lambda: False)()
                or getattr(current_user, "is_manager", lambda: False)()
                or getattr(current_user, "is_user", lambda: False)()
            ):
                show_points = True
            else:
                # Allow customer to view their own points if email matches
                try:
                    if (
                        getattr(current_user, "email", None)
                        and getattr(customer_obj, "email", None)
                        and current_user.email.lower() == customer_obj.email.lower()
                    ):
                        show_points = True
                except Exception:
                    show_points = False
    except Exception:
        show_points = False

    # If allowed, fetch recent loyalty transactions for quick view
    recent_transactions = []
    if show_points and loyalty:
        try:
            from .models import LoyaltyTransaction

            recent_transactions = (
                db.session.query(LoyaltyTransaction)
                .filter(LoyaltyTransaction.customer_loyalty_id == loyalty.id)
                .order_by(LoyaltyTransaction.created_at.desc())
                .limit(10)
                .all()
            )
        except Exception:
            recent_transactions = []
    return render_template(
        "customer_view.html",
        user=current_user,
        customer=customer_obj,
        laundries=laundries,
        laundries_page=laundries_page,
        total_laundries=total_laundries,
        loyalty=loyalty,
        total_earned=total_earned,
        total_points_today=total_points_today,
        total_points_redeemed=total_points_redeemed,
        show_points=show_points,
        recent_transactions=recent_transactions,
    )


def validate_phone_number(phone):
    """Validate Philippine phone number format"""
    if not phone:
        return False
    # Allow +639XXXXXXXXX or 09XXXXXXXXX formats
    phone_pattern = r"^(\+63|0)[0-9]{10}$"
    return bool(re.match(phone_pattern, phone))


def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional
    email_pattern = r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
    return bool(re.match(email_pattern, email, re.IGNORECASE))


@customer.route("/list")
@user_or_admin_required
def list_customers():
    # Get search and pagination parameters
    search_query = request.args.get("search", "").strip()
    # Remove pagination and limit
    sort_by = request.args.get("sort_by", "name")  # name, email, date_created
    sort_order = request.args.get("sort_order", "asc")  # asc, desc

    # Start with base query
    query = Customer.query

    # Apply search filter (search across name, email, and phone)
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term),
            )
        )

    # Apply sorting
    if sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(Customer.full_name.desc())
        else:
            query = query.order_by(Customer.full_name.asc())
    elif sort_by == "email":
        if sort_order == "desc":
            query = query.order_by(Customer.email.desc())
        else:
            query = query.order_by(Customer.email.asc())
    elif sort_by == "date_created":
        if sort_order == "desc":
            query = query.order_by(Customer.date_created.desc())
        else:
            query = query.order_by(Customer.date_created.asc())
    else:  # Default to name
        query = query.order_by(Customer.full_name.asc())

    customers = type("obj", (object,), {})()
    customers.items = query.all()
    customers.total = len(customers.items)
    customers.page = 1
    customers.pages = 1

    # Get total customer count for display
    total_customers = Customer.query.count()

    return render_template(
        "customer_list.html",
        user=current_user,
        customers=customers,
        total_customers=total_customers,
        search_query=search_query,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@customer.route("/add", methods=["GET", "POST"])
@user_or_admin_required
def add_customer():
    if request.method == "POST":
        full_name = request.form.get("fullName")
        email = request.form.get("email")
        phone = request.form.get("phone")
    

        # Validation
        errors = []

        if not full_name or len(full_name.strip()) < 2:
            errors.append("Full name must be at least 2 characters long.")

        if not phone or not validate_phone_number(phone):
            errors.append(
                "Please enter a valid Philippine phone number (e.g., +639123456789 or 09123456789)."
            )

        if email and not validate_email(email):
            errors.append("Please enter a valid email address.")

        if errors:
            for error in errors:
                flash(error, category="error")
        else:
            # Clean the data
            full_name = full_name.strip()
            email = email.strip() if email else None
            phone = phone.strip()

            # Create new customer with proper attribute assignment
            new_customer = Customer()
            new_customer.full_name = full_name
            new_customer.email = email
            new_customer.phone = phone

            db.session.add(new_customer)
            db.session.commit()
            # Broadcast notification to all users
            from app.models import Notification, User

            users = User.query.filter_by(is_active=True).all()
            for user in users:
                notif = Notification(
                    user_id=user.id,
                    title="New Customer Added",
                    message=f"Customer '{full_name}' has been added to the system.",
                    notification_type="info",
                    related_model="customer",
                    related_id=str(new_customer.id),
                    action_url=f"/customer/view/{new_customer.id}",
                    action_text="View Customer",
                )
                db.session.add(notif)
            db.session.commit()

            # Send welcome SMS if phone number is provided
            if phone:
                send_welcome_sms(new_customer)

            flash("Customer added successfully!", category="success")
            return redirect(url_for("customer.list_customers"))

    return render_template("customer_add.html", user=current_user)


@customer.route("/edit/<int:id>", methods=["GET", "POST"])
@user_or_admin_required
def edit_customer(id):
    customer_obj = Customer.query.get_or_404(id)

    if request.method == "POST":
        full_name = request.form.get("fullName")
        email = request.form.get("email")
        phone = request.form.get("phone")
        # Active/Inactive toggle from form (checkbox returns 'on' when checked)
        is_active_val = request.form.get("is_active")

        # Validation
        errors = []

        if not full_name or len(full_name.strip()) < 2:
            errors.append("Full name must be at least 2 characters long.")

        if not phone or not validate_phone_number(phone):
            errors.append(
                "Please enter a valid Philippine phone number (e.g., +639123456789 or 09123456789)."
            )

        if email and not validate_email(email):
            errors.append("Please enter a valid email address.")

        if errors:
            for error in errors:
                flash(error, category="error")
        else:
            # Clean and update the data
            customer_obj.full_name = full_name.strip()
            customer_obj.email = email.strip() if email else None
            customer_obj.phone = phone.strip()
            # Update active status if provided in the form
            try:
                customer_obj.is_active = str(is_active_val).lower() in ("on", "true", "1")
            except Exception:
                # Keep previous value on error
                pass

            db.session.commit()
            flash("Customer updated successfully!", category="success")
            return redirect(url_for("customer.list_customers"))

    return render_template("customer_edit.html", user=current_user, customer=customer_obj)


@customer.route("/toggle_status/<int:id>", methods=["GET", "POST"])
@user_or_admin_required
def toggle_status(id):
    customer_obj = Customer.query.get_or_404(id)
    # Toggle
    customer_obj.is_active = not customer_obj.is_active
    db.session.commit()

    # If AJAX/JSON request, return JSON payload so client can update in-page
    want_json = False
    try:
        if request.is_json:
            want_json = True
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            want_json = True
        else:
            # allow explicit ajax flag in JSON body
            j = request.get_json(silent=True)
            if isinstance(j, dict) and j.get('ajax'):
                want_json = True
    except Exception:
        want_json = False

    if want_json:
        return jsonify({
            'status': 'success',
            'is_active': bool(customer_obj.is_active),
            'customer_id': customer_obj.id,
        })

    status = "enabled" if customer_obj.is_active else "disabled"
    flash(f"Customer {customer_obj.full_name} has been {status}!", category="success")
    return redirect(url_for("customer.list_customers"))


@customer.route("/export")
@login_required
def export_customers():
    # Server-side permission enforcement: only admins and managers may export
    if not (current_user.is_admin() or current_user.is_manager()):
        return jsonify({"error": "forbidden"}), 403
    # Get the same filters as list_customers
    search_query = request.args.get("search", "").strip()
    sort_by = request.args.get("sort_by", "name")
    sort_order = request.args.get("sort_order", "asc")

    # Start with base query
    query = Customer.query

    # Apply search filter
    if search_query:
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term),
            )
        )

    # Apply sorting
    if sort_by == "name":
        if sort_order == "desc":
            query = query.order_by(Customer.full_name.desc())
        else:
            query = query.order_by(Customer.full_name.asc())
    elif sort_by == "email":
        if sort_order == "desc":
            query = query.order_by(Customer.email.desc())
        else:
            query = query.order_by(Customer.email.asc())
    elif sort_by == "date_created":
        if sort_order == "desc":
            query = query.order_by(Customer.date_created.desc())
        else:
            query = query.order_by(Customer.date_created.asc())
    else:
        query = query.order_by(Customer.full_name.asc())

    # Get all customers (no pagination for export)
    customers = query.all()
    # Record audit log for export
    try:
        from .models import ExportAudit

        audit = ExportAudit()
        audit.user_id = (
            current_user.id
            if current_user and getattr(current_user, "id", None)
            else None
        )
        audit.search_query = search_query
        db.session.add(audit)
        db.session.commit()
    except Exception:
        # Do not block export on audit failures
        db.session.rollback()

    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        ["ID", "Full Name", "Email", "Phone", "Date Created", "Total Laundries"]
    )

    # Write customer data
    # Compute laundries_count for all exported customers in a single query to avoid N+1
    from sqlalchemy import func

    cust_ids = [c.id for c in customers]
    counts = {}
    if cust_ids:
        rows = (
            db.session.query(Laundry.customer_id, func.count(Laundry.id))
            .filter(Laundry.customer_id.in_(cust_ids))
            .group_by(Laundry.customer_id)
            .all()
        )
        counts = {r[0]: r[1] for r in rows}

    for customer in customers:
        writer.writerow(
            [
                customer.id,
                customer.full_name,
                customer.email or "",
                customer.phone or "",
                customer.date_created.strftime("%Y-%m-%d %H:%M:%S"),
                counts.get(customer.id, 0),
            ]
        )

    # Create response
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = "attachment; filename=customers.csv"

    return response
