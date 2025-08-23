from flask import Blueprint, jsonify, render_template, request, session
from flask_login import current_user, login_required

from . import db, socketio
from .decorators import user_or_admin_required
from .models import (
    Customer,
    DashboardWidget,
    Expense,
    InventoryItem,
    Laundry,
    LaundryStatusHistory,
    Service,
)
from .sms_service import sms_service
from datetime import datetime, timedelta

from sqlalchemy import desc, func

views = Blueprint("views", __name__)


# New professional List View layout for customer directory
@views.route("/customer/list")
@login_required
def customer_list():
    return render_template("customer/list_view.html")


# New paginated, searchable Customer Directory API (search by name only)
@views.route("/api/customers", methods=["GET"])
def api_customers():
    # Return JSON 401 for unauthenticated API callers (prevents HTML login redirects)
    if not current_user.is_authenticated:
        return jsonify({"error": "unauthenticated"}), 401
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "", type=str).strip()
    sort_by = request.args.get("sort_by", "date_created", type=str)
    sort_order = request.args.get("sort_order", "desc", type=str)

    # Special-case sorting by laundries_count: use grouped query and paginate that result
    if sort_by == "laundries_count":
        from sqlalchemy import func

        # Build grouped query: (Customer, laundries_count)
        grouped = db.session.query(
            Customer, func.count(Laundry.id).label("laundries_count")
        ).outerjoin(Laundry, Laundry.customer_id == Customer.id)
        if search:
            search_like = f"%{search}%"
            grouped = grouped.filter(Customer.full_name.ilike(search_like))
        grouped = grouped.group_by(Customer.id)
        if sort_order == "desc":
            grouped = grouped.order_by(func.count(Laundry.id).desc())
        else:
            grouped = grouped.order_by(func.count(Laundry.id).asc())

        paged = grouped.paginate(page=page, per_page=per_page, error_out=False)
        total = paged.total
        results = []
        for row in paged.items:
            cust = row[0]
            cnt = row[1] or 0
            results.append(
                {
                    "id": cust.id,
                    "full_name": cust.full_name,
                    "email": cust.email,
                    "phone": cust.phone,
                    "laundries_count": cnt,
                    "is_active": cust.is_active,
                    "date_created": (
                        cust.date_created.strftime("%Y-%m-%d %H:%M:%S")
                        if cust.date_created
                        else None
                    ),
                }
            )

        return jsonify(
            {
                "results": results,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": paged.pages,
            }
        )

    # Default / simple sorting: query Customers and paginate
    query = Customer.query
    if search:
        search_like = f"%{search}%"
        query = query.filter(Customer.full_name.ilike(search_like))

    # Apply simple sorting options on Customer fields
    if sort_by == "name":
        query = query.order_by(
            Customer.full_name.desc()
            if sort_order == "desc"
            else Customer.full_name.asc()
        )
    elif sort_by == "email":
        query = query.order_by(
            Customer.email.desc() if sort_order == "desc" else Customer.email.asc()
        )
    else:
        # date_created (default)
        query = query.order_by(
            Customer.date_created.desc()
            if sort_order == "desc"
            else Customer.date_created.asc()
        )

    customers = query.paginate(page=page, per_page=per_page, error_out=False)
    total = customers.total

    # Attach laundries count for the returned page to avoid N+1 queries
    customer_ids = [c.id for c in customers.items]
    from sqlalchemy import func

    laundry_counts = {}
    if customer_ids:
        rows = (
            db.session.query(Laundry.customer_id, func.count(Laundry.id))
            .filter(Laundry.customer_id.in_(customer_ids))
            .group_by(Laundry.customer_id)
            .all()
        )
        laundry_counts = {r[0]: r[1] for r in rows}

    results = [
        {
            "id": c.id,
            "full_name": c.full_name,
            "email": c.email,
            "phone": c.phone,
            "laundries_count": laundry_counts.get(c.id, 0),
            "is_active": c.is_active,
            "date_created": (
                c.date_created.strftime("%Y-%m-%d %H:%M:%S") if c.date_created else None
            ),
        }
        for c in customers.items
    ]
    return jsonify(
        {
            "results": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": customers.pages,
        }
    )


@views.route("/api/push-notification", methods=["POST"])
@login_required
def push_notification():
    data = request.get_json()
    message = data.get("message", "")
    type_ = data.get("type", "info")
    # Emit notification to all connected clients
    socketio.emit(
        "push_notification", {"message": message, "type": type_}, broadcast=True
    )
    return jsonify({"success": True})




@views.route("/daily-calendar")
@login_required
def daily_calendar():
    # Get current month and year
    today = datetime.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    # Get first and last day of the month
    first_day = datetime(year, month, 1)
    if month == 12:
        next_month_dt = datetime(year + 1, 1, 1)
    else:
        next_month_dt = datetime(year, month + 1, 1)
    _last_day = next_month_dt - timedelta(days=1)

    # Query daily laundry totals
    daily_totals = (
        db.session.query(
            func.date(Laundry.date_received).label("day"),
            func.count(Laundry.laundry_id).label("total"),
        )
        .filter(
            Laundry.date_received >= first_day, Laundry.date_received < next_month_dt
        )
        .group_by(func.date(Laundry.date_received))
        .all()
    )

    # Build a dict for easy lookup
    totals_by_day = {str(day): total for day, total in daily_totals}

    # Prepare calendar grid
    import calendar

    cal = calendar.Calendar()
    month_days = cal.itermonthdays(year, month)
    month_grid = []
    week = []
    for day in month_days:
        if day == 0:
            week.append(None)
        else:
            date_str = f"{year}-{month:02d}-{day:02d}"
            week.append(
                {"day": day, "date": date_str, "total": totals_by_day.get(date_str, 0)}
            )
        if len(week) == 7:
            month_grid.append(week)
            week = []
    if week:
        month_grid.append(week)

    # Calculate previous and next month/year
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    return render_template(
        "daily_calendar.html",
        year=year,
        month=month,
        month_grid=month_grid,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year,
    )


# Laundry status settings API endpoints
@views.route("/api/laundry-status-settings", methods=["POST"])
@login_required
def save_laundry_status_settings():
    data = request.get_json()
    session["laundry_status_settings"] = data.get("enabled_statuses", [])
    return jsonify({"success": True})


@views.route("/api/laundry-status-settings", methods=["GET"])
@login_required
def get_laundry_status_settings():
    enabled_statuses = session.get(
        "laundry_status_settings", ["Received", "Ready for Pickup", "Completed"]
    )
    return jsonify({"enabled_statuses": enabled_statuses})


def get_default_widgets(role):
    """Get default widgets based on user role"""
    if role == "super_admin":
        # Super Admin: Full system access including financial, user management, and system settings
        return [
            "total_customers",
            "active_laundries",
            "completed_laundries",
            "total_revenue",
            "estimated_revenue",
            "total_services",
            "recent_expenses",
            "inventory_alerts",
            "user_management",
        ]
    elif role == "admin":
        # Admin: Full operational access including financial reports
        return [
            "total_customers",
            "active_laundries",
            "completed_laundries",
            "total_revenue",
            "estimated_revenue",
            "total_services",
            "recent_expenses",
            "inventory_alerts",
        ]
    elif role == "manager":
        # Manager: Operational oversight with limited financial access
        return [
            "total_customers",
            "active_laundries",
            "completed_laundries",
            "total_revenue",
            "total_services",
            "inventory_alerts",
            "service_performance",
        ]
    else:  # Employee
        # Employee: Basic operational access
        return ["active_laundries", "completed_laundries", "total_services", "my_tasks"]


def get_role_based_widgets(user_id):
    """Get user's widget configuration based on their role and preferences"""
    user = current_user

    # Get user's custom widgets or default based on role
    custom_widgets = DashboardWidget.query.filter_by(
        user_id=user_id, is_visible=True
    ).all()

    if custom_widgets:
        # Return user's custom widget configuration
        return [
            w.widget_id for w in sorted(custom_widgets, key=lambda x: x.position or 0)
        ]
    else:
        # Return default widgets for user's role
        return get_default_widgets(user.role)


def get_user_dashboard_config(user_id):
    """Get user's dashboard widget configuration"""
    return get_role_based_widgets(user_id)


@views.route("/")
@login_required
def dashboard():
    today = datetime.now().date()
    # Calculate today's earned amount for statuses Received, Ready to Pickup, Completed
    today_earned_all_status = (
        db.session.query(func.sum(Laundry.price))
        .filter(
            func.date(Laundry.date_updated) == today,
            Laundry.status.in_(["Received", "Ready for Pickup", "Completed"]),
        )
        .scalar()
        or 0
    )
    # Count laundries with status 'Ready for Pickup' (all, no date filter)
    ready_pickup_count = Laundry.query.filter_by(status="Ready for Pickup").count()
    # Count laundries with status 'Received' for new dashboard card
    received_laundries_count = Laundry.query.filter_by(status="Received").count()
    # Count laundries with status 'Pending' and 'Received' for dashboard cards
    pending_since_beginning = Laundry.query.filter_by(status="Pending").count()
    active_laundries_received_status = Laundry.query.filter_by(
        status="Received"
    ).count()
    # Total laundries with status 'Received' (since beginning)
    _received_since_beginning = Laundry.query.filter_by(status="Received").count()
    # Calculate today's earnings (visible to all users)
    # Definition: sum of prices for orders whose status transitioned to 'Completed' or 'Picked Up' today
    today = datetime.now().date()
    # Active laundries received today (not completed or picked up)
    active_laundries_received_today = Laundry.query.filter(
        func.date(Laundry.date_received) == today,
        ~Laundry.status.in_(["Completed", "Picked Up"]),
    ).count()
    # Active laundries pending since the beginning (never updated from 'Pending')
    pending_since_beginning = Laundry.query.filter_by(status="Pending").count()
    # Get user's customized dashboard widgets based on role
    user_widgets = get_user_dashboard_config(current_user.id)

    # Initialize dashboard data dictionary
    dashboard_data = {}
    # Get business address for weather lookup
    from .models import BusinessSettings

    business_settings = BusinessSettings.query.first()
    address = (
        business_settings.address if business_settings else "Butuan City, Philippines"
    )

    # Fetch live weather from WeatherAPI
    import requests

    weather_api_key = "48919a57b3364a6a96b234041251708"
    weather_url = (
        f"https://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={address}"
    )
    try:
        weather_resp = requests.get(weather_url, timeout=5)
        if weather_resp.status_code == 200:
            weather_json = weather_resp.json()
            temp_c = weather_json["current"]["temp_c"]
            condition = weather_json["current"]["condition"]["text"]
            icon = weather_json["current"]["condition"]["icon"]
            dashboard_data["weather_today"] = f"{condition}, {temp_c}°C"
            dashboard_data["weather_icon"] = icon
        else:
            dashboard_data["weather_today"] = "Weather unavailable"
            dashboard_data["weather_icon"] = ""
    except Exception:
        dashboard_data["weather_today"] = "Weather unavailable"
        dashboard_data["weather_icon"] = ""

    # Common data for all users
    # Treat 'Picked Up' as completed/not active as well
    active_laundries = Laundry.query.filter(
        ~Laundry.status.in_(["Completed", "Picked Up"])
    ).count()
    completed_laundries = Laundry.query.filter_by(status="Completed").count()
    # Services: track both total and active for utilization
    total_services = Service.query.count()
    active_services = Service.query.filter_by(is_active=True).count()

    # Recent laundries (limit view to 6) - available to all users
    RECENT_LIMIT = 6
    recent_laundries = (
        Laundry.query.order_by(Laundry.date_received.desc()).limit(RECENT_LIMIT).all()
    )
    total_laundries_count = Laundry.query.count()
    recent_laundries_more = max(0, total_laundries_count - RECENT_LIMIT)

    # Calculate today's earnings (visible to all users)
    # Definition: sum of prices for orders whose status transitioned to 'Completed' or 'Picked Up' today
    today = datetime.now().date()
    completed_today_subq = (
        db.session.query(LaundryStatusHistory.laundry_id)
        .filter(
            LaundryStatusHistory.new_status.in_(["Completed", "Ready for Pickup"]),
            func.date(LaundryStatusHistory.changed_at) == today,
        )
        .subquery()
    )
    today_earnings = (
        db.session.query(func.sum(Laundry.price))
        .filter(Laundry.laundry_id.in_(completed_today_subq))
        .scalar()
        or 0
    )

    # Count of orders completed today (via status history), includes 'Picked Up'
    completed_today = (
        db.session.query(func.count(func.distinct(LaundryStatusHistory.laundry_id)))
        .filter(
            LaundryStatusHistory.new_status.in_(["Completed", "Ready for Pickup"]),
            func.date(LaundryStatusHistory.changed_at) == today,
        )
        .scalar()
        or 0
    )

    # Calculate laundries received today
    received_today = Laundry.query.filter(
        func.date(Laundry.date_received) == today
    ).count()

    # Add common data to dashboard_data
    dashboard_data.update(
        {
            "pending_since_beginning": pending_since_beginning,
            "active_laundries": active_laundries,
            "active_laundries_received_status": active_laundries_received_status,
            "active_laundries_received_today": active_laundries_received_today,
            "received_laundries_count": received_laundries_count,
            "ready_pickup_count": ready_pickup_count,
            "today_earned_all_status": today_earned_all_status,
            "completed_laundries": completed_laundries,
            "total_services": total_services,
            "active_services": active_services,
            "recent_laundries": recent_laundries,
            "recent_laundries_more": recent_laundries_more,
            "today_earnings": today_earnings,
            "completed_today": completed_today,
            "received_today": received_today,
        }
    )
    # ...existing code...
    # Quick performance metrics (last 7 days)
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)

    # New customers last 7 days and previous 7 days for growth
    new_customers_7d = Customer.query.filter(
        Customer.date_created >= seven_days_ago
    ).count()
    prev_customers_7d = Customer.query.filter(
        Customer.date_created >= fourteen_days_ago,
        Customer.date_created < seven_days_ago,
    ).count()
    if prev_customers_7d > 0:
        customer_growth_percent = round(
            ((new_customers_7d - prev_customers_7d) / prev_customers_7d) * 100
        )
    else:
        customer_growth_percent = 100 if new_customers_7d > 0 else 0

    laundries_7d_total = Laundry.query.filter(
        Laundry.date_received >= seven_days_ago
    ).count()
    laundries_7d_completed = Laundry.query.filter(
        Laundry.date_received >= seven_days_ago, Laundry.status == "Completed"
    ).count()
    completion_rate_7d = (
        round((laundries_7d_completed / laundries_7d_total) * 100)
        if laundries_7d_total > 0
        else 0
    )

    # Capacity percent for visualization (assumes 50 as nominal capacity)
    capacity_percent = (
        round(min(100, (active_laundries / 50) * 100))
        if active_laundries is not None
        else 0
    )

    # Service utilization (active vs total defined services)
    service_utilization_percent = (
        round((active_services / total_services) * 100) if total_services > 0 else 0
    )

    # Business health score based on recent performance and utilization
    # Weighted blend: completion rate (40%), customer growth (30%), service utilization (30%)
    def clamp(v, lo=0, hi=100):
        return max(lo, min(hi, v))

    business_health_score = clamp(
        round(
            0.4 * clamp(completion_rate_7d)
            + 0.3 * clamp(customer_growth_percent)
            + 0.3 * clamp(service_utilization_percent)
        )
    )

    # Get laundries completed or ready for pickup today by status change date
    completed_today_laundry_rows = (
        db.session.query(LaundryStatusHistory.laundry_id)
        .filter(
            LaundryStatusHistory.new_status.in_(["Completed", "Ready for Pickup"]),
            func.date(LaundryStatusHistory.changed_at) == today,
        )
        .distinct()
        .all()
    )
    completed_today_laundry_ids = [
        row.laundry_id for row in completed_today_laundry_rows
    ]
    _completed_today_laundries = Laundry.query.filter(
        Laundry.laundry_id.in_(completed_today_laundry_ids)
    ).all()
    dashboard_data.update(
        {
            "new_customers_7d": new_customers_7d,
            "customer_growth_percent": customer_growth_percent,
            "completion_rate_7d": completion_rate_7d,
            "capacity_percent": capacity_percent,
            "service_utilization_percent": service_utilization_percent,
            "business_health_score": business_health_score,
        }
    )

    # Role-based data access
    if current_user.is_admin():
        # Full admin access - all data including financial and system info
        total_customers = Customer.query.count()
        total_revenue = (
            db.session.query(func.sum(Laundry.price))
            .filter(Laundry.status.in_(["Completed", "Ready for Pickup"]))
            .scalar()
            or 0
        )
        estimated_revenue = (
            db.session.query(func.sum(Laundry.price))
            .filter(~Laundry.status.in_(["Completed", "Ready for Pickup"]))
            .scalar()
            or 0
        )

        # Popular services (admin only)
        popular_services = (
            db.session.query(Service.name, func.count(Laundry.id).label("count"))
            .join(Service.laundries)
            .group_by(Service.id)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # Recent expenses (admin only) limited to 6 for professional compact view
        recent_expenses = (
            Expense.query.order_by(Expense.expense_date.desc())
            .limit(RECENT_LIMIT)
            .all()
        )
        total_expenses_count = Expense.query.count()
        recent_expenses_more = max(0, total_expenses_count - RECENT_LIMIT)

        # Add admin-specific data
        dashboard_data.update(
            {
                "total_customers": total_customers,
                "total_revenue": total_revenue,
                "estimated_revenue": estimated_revenue,
                "popular_services": popular_services,
                "recent_expenses": recent_expenses,
                "recent_expenses_more": recent_expenses_more,
            }
        )
    elif current_user.is_manager():
        # Manager access - operational data and reports but limited financial access
        total_customers = Customer.query.count()
        total_revenue = (
            db.session.query(func.sum(Laundry.price))
            .filter(Laundry.status.in_(["Completed", "Ready for Pickup"]))
            .scalar()
            or 0
        )
        estimated_revenue = (
            db.session.query(func.sum(Laundry.price))
            .filter(~Laundry.status.in_(["Completed", "Ready for Pickup"]))
            .scalar()
            or 0
        )

        # Popular services (manager access)
        popular_services = (
            db.session.query(Service.name, func.count(Laundry.id).label("count"))
            .join(Service.laundries)
            .group_by(Service.id)
            .order_by(desc("count"))
            .limit(5)
            .all()
        )

        # Recent expenses limited for managers (no sensitive financial data)
        recent_expenses = []
        recent_expenses_more = 0

        # Add manager-specific data
        dashboard_data.update(
            {
                "total_customers": total_customers,
                "total_revenue": total_revenue,
                "estimated_revenue": estimated_revenue,
                "popular_services": popular_services,
                "recent_expenses": recent_expenses,
                "recent_expenses_more": recent_expenses_more,
            }
        )
    else:
        # User access - show total customers, hide financials
        total_customers = Customer.query.count()
        dashboard_data.update(
            {
                "total_customers": total_customers,
                "total_revenue": 0,
                "estimated_revenue": 0,
                "popular_services": [],
                "recent_expenses": [],
                "recent_expenses_more": 0,
            }
        )

    # Get all active services for pricing display (available to all users)
    all_services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.category, Service.name)
        .all()
    )
    dashboard_data["all_services"] = all_services

    # Admin-only statistics and charts
    if current_user.is_admin():
        # Get inventory statistics (admin only)
        total_inventory_items = InventoryItem.query.filter_by(is_active=True).count()
        low_stock_items = InventoryItem.query.filter(
            InventoryItem.current_stock <= InventoryItem.minimum_stock,  # type: ignore
            InventoryItem.is_active,  # type: ignore
        ).all()
        out_of_stock_items = InventoryItem.query.filter(
            InventoryItem.current_stock <= 0,  # type: ignore
            InventoryItem.is_active,  # type: ignore
        ).all()

        # Calculate total inventory value
        total_inventory_value = (
            db.session.query(
                func.sum(InventoryItem.current_stock * InventoryItem.cost_per_unit)
            )
            .filter(InventoryItem.is_active)
            .scalar()
            or 0
        )  # type: ignore

        # Additional stats for charts
        pending_laundries = Laundry.query.filter_by(status="Pending").count()
        in_progress_laundries = Laundry.query.filter_by(status="In Progress").count()
        picked_up_laundries = Laundry.query.filter_by(status="Picked Up").count()

        # Service type counts
        wash_only_services = Service.query.filter(
            Service.category == "Standard"
        ).count()
        dry_only_services = Service.query.filter(Service.category == "Express").count()
        wash_dry_services = Service.query.filter(Service.category == "Premium").count()

        # Add admin-specific data to dashboard_data
        dashboard_data.update(
            {
                "total_inventory_items": total_inventory_items,
                "low_stock_items": low_stock_items,
                "out_of_stock_items": out_of_stock_items,
                "total_inventory_value": total_inventory_value,
                "pending_laundries": pending_laundries,
                "in_progress_laundries": in_progress_laundries,
                "picked_up_laundries": picked_up_laundries,
            }
        )

        # Prepare chart data as clean JSON objects (admin only)
        chart_data = {
            "revenue": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [
                    round(dashboard_data["total_revenue"] * 0.6, 2),
                    round(dashboard_data["total_revenue"] * 0.7, 2),
                    round(dashboard_data["total_revenue"] * 0.8, 2),
                    round(dashboard_data["total_revenue"] * 0.9, 2),
                    round(dashboard_data["total_revenue"] * 0.95, 2),
                    round(dashboard_data["total_revenue"], 2),
                ],
            },
            "services": {
                "labels": ["Standard", "Express", "Premium", "Other"],
                "data": [
                    wash_only_services,
                    dry_only_services,
                    wash_dry_services,
                    max(
                        0,
                        dashboard_data["total_services"]
                        - (wash_only_services + dry_only_services + wash_dry_services),
                    ),
                ],
            },
            "status": {
                "labels": ["Pending", "In Progress", "Completed", "Picked Up"],
                "data": [
                    pending_laundries,
                    in_progress_laundries,
                    dashboard_data["completed_laundries"],
                    picked_up_laundries,
                ],
            },
            "inventory": {
                "labels": ["Total Items", "Low Stock", "Out of Stock", "Healthy Stock"],
                "data": [
                    total_inventory_items,
                    len(low_stock_items),
                    len(out_of_stock_items),
                    max(
                        0,
                        total_inventory_items
                        - len(low_stock_items)
                        - len(out_of_stock_items),
                    ),
                ],
            },
        }
        dashboard_data["chart_data"] = chart_data
    else:
        # Regular users get simplified chart data
        dashboard_data.update(
            {
                "total_inventory_items": 0,
                "low_stock_items": [],
                "out_of_stock_items": [],
                "total_inventory_value": 0,
                "chart_data": {},
            }
        )

    # Prepare template data based on role
    template_data = {
        "user": current_user,
        "user_widgets": user_widgets,
        "datetime": datetime,  # Add datetime for template use
        "today": today,
        **dashboard_data,  # Unpack all dashboard data
    }

    return render_template("dashboard.html", **template_data)


@views.route("/charts")
@login_required
def charts():
    """Interactive Charts page"""
    # Get the same data as dashboard for charts
    total_customers = Customer.query.count()
    # Treat Picked Up as completed/non-active
    active_laundries = Laundry.query.filter(
        ~Laundry.status.in_(["Completed", "Picked Up"])
    ).count()
    completed_laundries = Laundry.query.filter_by(status="Completed").count()

    # Calculate real revenue from completed laundries
    total_revenue = (
        db.session.query(func.sum(Laundry.price))
        .filter(Laundry.status == "Completed")
        .scalar()
        or 0
    )

    # Get popular services data
    popular_services = (
        db.session.query(Service.name, func.count(Laundry.id).label("count"))
        .join(Service.laundries)
        .group_by(Service.id)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    # Service type counts
    _wash_only_services = Service.query.filter(Service.category == "Standard").count()
    _dry_only_services = Service.query.filter(Service.category == "Express").count()
    _wash_dry_services = Service.query.filter(Service.category == "Premium").count()
    _total_services = Service.query.filter_by(is_active=True).count()

    # Inventory summary metrics expected by template
    _total_inventory_items = InventoryItem.query.filter_by(is_active=True).count()
    low_stock_items_count = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.minimum_stock,  # type: ignore
        InventoryItem.is_active,  # type: ignore
    ).count()
    out_of_stock_items_count = InventoryItem.query.filter(
        InventoryItem.current_stock <= 0,  # type: ignore
        InventoryItem.is_active,  # type: ignore
    ).count()
    total_inventory_value = (
        db.session.query(
            func.sum(InventoryItem.current_stock * InventoryItem.cost_per_unit)
        )
        .filter(InventoryItem.is_active.is_(True))
        .scalar()
        or 0
    )

    # Replace heavy graph construction with compact trend metrics.
    # Trends summarize recent activity (7d, 30d) and compare to the previous window.
    try:
        today = datetime.utcnow().date()

        # 7-day window (last 7 days) and previous 7-day window
        last_7_start = today - timedelta(days=6)
        prev_7_start = last_7_start - timedelta(days=7)
        prev_7_end = last_7_start - timedelta(days=1)

        last_7_count = Laundry.query.filter(
            func.date(Laundry.date_received) >= last_7_start
        ).count()
        prev_7_count = Laundry.query.filter(
            func.date(Laundry.date_received) >= prev_7_start,
            func.date(Laundry.date_received) <= prev_7_end,
        ).count()
        if prev_7_count > 0:
            pct_change_7 = round(
                ((last_7_count - prev_7_count) / prev_7_count) * 100, 1
            )
        else:
            pct_change_7 = 100.0 if last_7_count > 0 else 0.0

        # 30-day revenue window and previous 30-day window
        last_30_start = today - timedelta(days=29)
        prev_30_start = last_30_start - timedelta(days=30)
        prev_30_end = last_30_start - timedelta(days=1)

        revenue_last_30 = (
            db.session.query(func.coalesce(func.sum(Laundry.price), 0))
            .filter(func.date(Laundry.date_received) >= last_30_start)
            .scalar()
            or 0
        )
        revenue_prev_30 = (
            db.session.query(func.coalesce(func.sum(Laundry.price), 0))
            .filter(
                func.date(Laundry.date_received) >= prev_30_start,
                func.date(Laundry.date_received) <= prev_30_end,
            )
            .scalar()
            or 0
        )
        if revenue_prev_30 > 0:
            pct_change_revenue_30 = round(
                ((revenue_last_30 - revenue_prev_30) / revenue_prev_30) * 100, 1
            )
        else:
            pct_change_revenue_30 = 100.0 if revenue_last_30 > 0 else 0.0

        # 30-day completion rate (Completed / total received)
        completed_last_30 = Laundry.query.filter(
            func.date(Laundry.date_received) >= last_30_start,
            Laundry.status == "Completed",
        ).count()
        total_last_30 = Laundry.query.filter(
            func.date(Laundry.date_received) >= last_30_start
        ).count()
        completion_rate_30 = (
            round((completed_last_30 / total_last_30) * 100, 1)
            if total_last_30 > 0
            else 0.0
        )

        completed_prev_30 = Laundry.query.filter(
            func.date(Laundry.date_received) >= prev_30_start,
            func.date(Laundry.date_received) <= prev_30_end,
            Laundry.status == "Completed",
        ).count()
        total_prev_30 = Laundry.query.filter(
            func.date(Laundry.date_received) >= prev_30_start,
            func.date(Laundry.date_received) <= prev_30_end,
        ).count()
        completion_prev_rate_30 = (
            round((completed_prev_30 / total_prev_30) * 100, 1)
            if total_prev_30 > 0
            else 0.0
        )
        if completion_prev_rate_30 > 0:
            pct_change_completion_30 = round(
                (
                    (completion_rate_30 - completion_prev_rate_30)
                    / completion_prev_rate_30
                )
                * 100,
                1,
            )
        else:
            pct_change_completion_30 = 100.0 if completion_rate_30 > 0 else 0.0

        trends = {
            "laundries_7d": {
                "count": last_7_count,
                "previous_count": prev_7_count,
                "pct_change": pct_change_7,
            },
            "revenue_30d": {
                "amount": float(revenue_last_30),
                "previous_amount": float(revenue_prev_30),
                "pct_change": pct_change_revenue_30,
            },
            "completion_rate_30d": {
                "rate": completion_rate_30,
                "previous_rate": completion_prev_rate_30,
                "pct_change": pct_change_completion_30,
            },
        }

        # Keep backwards-compatible chart_data wrapper but replace content with trends
        chart_data = {"trends": trends}
    except Exception:
        # If trends calculation fails, fall back to an empty trends structure so the page doesn't break
        chart_data = {
            "trends": {"laundries_7d": {}, "revenue_30d": {}, "completion_rate_30d": {}}
        }

    # Real transactions and earnings analytics
    try:
        from collections import defaultdict
        from datetime import date as _date

        today = _date.today()

        # Helper: build a price map for a set of laundry_ids
        def build_price_map(laundry_ids: set[str]) -> dict[str, float]:
            if not laundry_ids:
                return {}
            rows = Laundry.query.filter(Laundry.laundry_id.in_(list(laundry_ids))).all()
            return {row.laundry_id: float((row.price or 0.0)) for row in rows}

        # Daily (last 7 days) using Python aggregation for portability
        days_back = 7
        start_daily = today - timedelta(days=days_back - 1)
        daily_hist = (
            db.session.query(
                func.date(LaundryStatusHistory.changed_at).label("day"),
                LaundryStatusHistory.laundry_id,
            )
            .filter(
                LaundryStatusHistory.new_status.in_(["Completed", "Picked Up"]),
                func.date(LaundryStatusHistory.changed_at) >= start_daily,
                func.date(LaundryStatusHistory.changed_at) <= today,
            )
            .all()
        )

        # Aggregate by day with distinct laundries per day
        daily_ids_by_day: dict[str, set[str]] = defaultdict(set)
        daily_hist_ids_window: set[str] = set()
        for day_val, lid in daily_hist:
            key = str(day_val)
            daily_ids_by_day[key].add(lid)
            daily_hist_ids_window.add(lid)

        # Fallback: include laundries with status Completed/Picked Up by date_updated if missing in history
        daily_fallback_rows = (
            Laundry.query.with_entities(
                func.date(Laundry.date_updated).label("day"), Laundry.laundry_id
            )
            .filter(
                Laundry.status.in_(["Completed", "Picked Up"]),
                func.date(Laundry.date_updated) >= start_daily,
                func.date(Laundry.date_updated) <= today,
            )
            .all()
        )
        for fday, flid in daily_fallback_rows:
            if flid not in daily_hist_ids_window:
                key = str(fday)
                daily_ids_by_day[key].add(flid)

        # Build price map for all laundries appearing in window
        all_daily_ids: set[str] = set()
        for s in daily_ids_by_day.values():
            all_daily_ids.update(s)
        price_map_daily = build_price_map(all_daily_ids)

        daily_labels: list[str] = []
        daily_counts: list[int] = []
        daily_earnings: list[float] = []
        for i in range(days_back):
            d = start_daily + timedelta(days=i)
            key = d.isoformat()
            daily_labels.append(d.strftime("%b %d"))
            lids = daily_ids_by_day.get(key, set())
            daily_counts.append(len(lids))
            revenue = sum(price_map_daily.get(lx, 0.0) for lx in lids)
            daily_earnings.append(round(revenue, 2))

        # Weekly (last 6 weeks) - aggregate in Python for cross-DB compatibility
        weeks_back = 6
        start_weekly = today - timedelta(
            weeks=weeks_back - 1, days=today.weekday()
        )  # start of week (Mon)
        weekly_histories = (
            db.session.query(
                LaundryStatusHistory.laundry_id, LaundryStatusHistory.changed_at
            )
            .filter(
                LaundryStatusHistory.new_status.in_(["Completed", "Picked Up"]),
                func.date(LaundryStatusHistory.changed_at) >= start_weekly,
                func.date(LaundryStatusHistory.changed_at) <= today,
            )
            .all()
        )

        weekly_counts_map: dict[str, int] = defaultdict(int)
        weekly_ids_map: dict[str, set[str]] = defaultdict(set)
        weekly_hist_ids_window: set[str] = set()
        for lid, changed_at in weekly_histories:
            week_year, week_num, _ = changed_at.isocalendar()
            key = f"{week_year}-W{week_num:02d}"
            if lid not in weekly_ids_map[key]:
                weekly_ids_map[key].add(lid)
                weekly_counts_map[key] += 1
                weekly_hist_ids_window.add(lid)

        # Fallback: add laundries using date_updated week if not present in history
        weekly_fallback_rows = (
            Laundry.query.with_entities(Laundry.laundry_id, Laundry.date_updated)
            .filter(
                Laundry.status.in_(["Completed", "Picked Up"]),
                func.date(Laundry.date_updated) >= start_weekly,
                func.date(Laundry.date_updated) <= today,
            )
            .all()
        )
        for lid, upd in weekly_fallback_rows:
            if lid in weekly_hist_ids_window:
                continue
            wy, wn, _ = upd.isocalendar()
            key = f"{wy}-W{wn:02d}"
            if lid not in weekly_ids_map[key]:
                weekly_ids_map[key].add(lid)
                weekly_counts_map[key] += 1

        # Build price map for all weekly ids
        all_weekly_ids: set[str] = set()
        for s in weekly_ids_map.values():
            all_weekly_ids.update(s)
        price_map_weekly = build_price_map(all_weekly_ids)

        weekly_labels: list[str] = []
        weekly_counts: list[int] = []
        weekly_earnings: list[float] = []
        cur = start_weekly
        for _ in range(weeks_back):
            wy, wn, _ = cur.isocalendar()
            label = f"{wy}-W{wn:02d}"
            weekly_labels.append(label)
            lids = weekly_ids_map.get(label, set())
            weekly_counts.append(len(lids))
            revenue = sum(price_map_weekly.get(lx, 0.0) for lx in lids)
            weekly_earnings.append(round(revenue, 2))
            cur = cur + timedelta(weeks=1)

        # Monthly (last 12 months) - aggregate in Python
        months_back = 12

        # Helper to move months without external deps
        def add_months(y: int, m: int, delta: int) -> tuple[int, int]:
            total = y * 12 + (m - 1) + delta
            ny = total // 12
            nm = total % 12 + 1
            return ny, nm

        sy, sm = add_months(today.year, today.month, -(months_back - 1))
        start_month_date = datetime(sy, sm, 1).date()

        monthly_histories = (
            db.session.query(
                LaundryStatusHistory.laundry_id, LaundryStatusHistory.changed_at
            )
            .filter(
                LaundryStatusHistory.new_status.in_(["Completed", "Picked Up"]),
                func.date(LaundryStatusHistory.changed_at) >= start_month_date,
                func.date(LaundryStatusHistory.changed_at) <= today,
            )
            .all()
        )

        monthly_ids_map: dict[str, set[str]] = defaultdict(set)
        monthly_hist_ids_window: set[str] = set()
        for lid, changed_at in monthly_histories:
            key = changed_at.strftime("%Y-%m")
            monthly_ids_map[key].add(lid)
            monthly_hist_ids_window.add(lid)

        # Fallback: use Laundry.date_updated month if not present in history
        monthly_fallback_rows = (
            Laundry.query.with_entities(Laundry.laundry_id, Laundry.date_updated)
            .filter(
                Laundry.status.in_(["Completed", "Picked Up"]),
                func.date(Laundry.date_updated) >= start_month_date,
                func.date(Laundry.date_updated) <= today,
            )
            .all()
        )
        for lid, upd in monthly_fallback_rows:
            if lid in monthly_hist_ids_window:
                continue
            key = upd.strftime("%Y-%m")
            monthly_ids_map[key].add(lid)

        # Build price map for all monthly ids
        all_monthly_ids: set[str] = set()
        for s in monthly_ids_map.values():
            all_monthly_ids.update(s)
        price_map_monthly = build_price_map(all_monthly_ids)

        monthly_labels: list[str] = []
        monthly_counts: list[int] = []
        monthly_earnings: list[float] = []
        cy, cm = sy, sm
        for _ in range(months_back):
            key = f"{cy:04d}-{cm:02d}"
            monthly_labels.append(datetime(cy, cm, 1).strftime("%b %Y"))
            lids = monthly_ids_map.get(key, set())
            monthly_counts.append(len(lids))
            revenue = sum(price_map_monthly.get(lx, 0.0) for lx in lids)
            monthly_earnings.append(round(revenue, 2))
            cy, cm = add_months(cy, cm, 1)

        chart_data.update(
            {
                "daily_transactions": {"labels": daily_labels, "data": daily_counts},
                "daily_earnings": {"labels": daily_labels, "data": daily_earnings},
                "weekly_transactions": {"labels": weekly_labels, "data": weekly_counts},
                "weekly_earnings": {"labels": weekly_labels, "data": weekly_earnings},
                "monthly_transactions": {
                    "labels": monthly_labels,
                    "data": monthly_counts,
                },
                "monthly_earnings": {
                    "labels": monthly_labels,
                    "data": monthly_earnings,
                },
            }
        )
    except Exception:
        # If any analytics fail, keep existing charts without breaking page
        pass

    return render_template(
        "charts.html",
        chart_data=chart_data,
        total_customers=total_customers,
        active_laundries=active_laundries,
        completed_laundries=completed_laundries,
        total_revenue=total_revenue,
        total_inventory_value=total_inventory_value,
        low_stock_items_count=low_stock_items_count,
        out_of_stock_items_count=out_of_stock_items_count,
        popular_services=popular_services,
    )


@views.route("/send_sms", methods=["POST"])
@login_required
@user_or_admin_required
def send_sms_route():
    try:
        data = request.get_json()
        phone_number = data.get("phone_number")
        message = data.get("message")

        if not phone_number or not message:
            return jsonify(
                {"success": False, "message": "Phone number and message are required"}
            )

        # Use the SMS service to send the message
        result = sms_service.send_sms(phone_number, message)

        if result:
            return jsonify({"success": True, "message": "SMS sent successfully"})
        else:
            return jsonify({"success": False, "message": "Failed to send SMS"})

    except Exception as e:
        return jsonify({"success": False, "message": f"Error sending SMS: {str(e)}"})


@views.route("/toggle_widget", methods=["POST"])
@login_required
def toggle_widget():
    """Toggle widget visibility for current user"""
    try:
        data = request.get_json()
        widget_id = data.get("widget_id")

        widget = DashboardWidget.query.filter_by(
            user_id=current_user.id, widget_id=widget_id
        ).first()

        if widget:
            widget.is_visible = not widget.is_visible
            db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "message": f'Widget {"shown" if widget.is_visible else "hidden"}',
                    "is_visible": widget.is_visible,
                }
            )
        else:
            return jsonify({"success": False, "message": "Widget not found"})

    except Exception as e:
        db.session.rollback()
        return jsonify(
            {"success": False, "message": f"Error toggling widget: {str(e)}"}
        )
