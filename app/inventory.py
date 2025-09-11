import os
import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for, send_file
from flask_login import current_user, login_required
from sqlalchemy import desc, func, or_
from io import StringIO, BytesIO
import csv
from werkzeug.utils import secure_filename

from . import db
from .models import InventoryCategory, InventoryItem, StockMovement

inventory = Blueprint("inventory", __name__)

# Configuration
UPLOAD_FOLDER = "app/static/uploads/inventory"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


# Restrict entire inventory module to managers/admins
@inventory.before_request
@login_required
def _inventory_access_guard():
    """Ensure only managers/admins (including admin/super_admin) can access inventory routes."""
    # current_user.is_manager() returns True for manager, admin, super_admin
    if not current_user.is_manager():
        flash("You do not have permission to access inventory.", "error")
        return redirect(url_for("views.dashboard"))


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file):
    """Save uploaded image and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename) if file.filename else "image.jpg"
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}_{name}{ext}"

        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        return unique_filename
    return None


def delete_image(filename):
    """Delete an image file"""
    if filename:
        try:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass  # Ignore errors when deleting


@inventory.route("/dashboard")
@login_required
def dashboard():
    """Inventory dashboard with overview statistics"""
    # Get summary statistics
    total_items = InventoryItem.query.count()
    total_categories = InventoryCategory.query.count()

    # Calculate total value
    items = InventoryItem.query.all()
    total_value = sum((item.cost_per_unit or 0) * item.current_stock for item in items)

    # Get low stock items
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.minimum_stock  # type: ignore
    ).all()
    low_stock_count = len(low_stock_items)

    # Get recent movements (last 10)
    recent_movements = (
        StockMovement.query.order_by(desc(StockMovement.created_at)).limit(10).all()
    )

    # Get categories for overview
    categories = InventoryCategory.query.all()

    return render_template(
        "inventory/dashboard.html",
        total_items=total_items,
        total_categories=total_categories,
        total_value=total_value,
        low_stock_count=low_stock_count,
        low_stock_items=low_stock_items,
        recent_movements=recent_movements,
        categories=categories,
    )


@inventory.route("/items")
@login_required
def list_items():
    """List all inventory items with filtering and pagination"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category", type=int)
    status_filter = request.args.get("status", "").strip()

    # Base query
    query = InventoryItem.query

    # Apply search filter
    if search:
        query = query.filter(
            or_(
                InventoryItem.name.ilike(f"%{search}%"),
                InventoryItem.sku.ilike(f"%{search}%"),
                InventoryItem.description.ilike(f"%{search}%"),
            )
        )

    # Apply category filter
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)  # type: ignore

    # Apply status filter
    if status_filter:
        if status_filter == "low_stock":
            query = query.filter(InventoryItem.current_stock <= InventoryItem.minimum_stock)  # type: ignore
        elif status_filter == "out_of_stock":
            query = query.filter(InventoryItem.current_stock <= 0)  # type: ignore
        elif status_filter == "in_stock":
            query = query.filter(InventoryItem.current_stock > InventoryItem.minimum_stock)  # type: ignore

    # Paginate results
    items = query.order_by(InventoryItem.name).paginate(
        page=page, per_page=20, error_out=False
    )

    # Get categories for filter dropdown
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()

    return render_template("inventory/items.html", items=items, categories=categories)


@inventory.route("/items/add", methods=["GET", "POST"])
@login_required
def add_item():
    """Add a new inventory item"""
    if request.method == "POST":
        try:
            # Get form data
            name = request.form.get("name", "").strip()
            sku = request.form.get("sku", "").strip() or None
            description = request.form.get("description", "").strip() or None
            category_id = request.form.get("category_id", type=int) or None
            new_category = request.form.get("new_category", "").strip()
            current_stock = request.form.get("current_stock", type=float) or 0
            minimum_stock = request.form.get("minimum_stock", type=float) or 0
            unit = request.form.get("unit", "").strip()
            unit_cost = request.form.get("unit_cost", type=float) or None

            # Handle image upload
            image_filename = None
            if "item_image" in request.files:
                file = request.files["item_image"]
                if file and file.filename:
                    image_filename = save_uploaded_image(file)
                    if image_filename is None:
                        flash(
                            "Invalid image file. Please upload PNG, JPG, JPEG, GIF, or WebP files.",
                            "error",
                        )
                        return redirect(url_for("inventory.add_item"))

            # Validate required fields
            if not name:
                flash("Item name is required", "error")
                return redirect(url_for("inventory.add_item"))

            if not unit:
                flash("Unit is required", "error")
                return redirect(url_for("inventory.add_item"))

            # Handle new category creation
            if new_category and not category_id:
                category = InventoryCategory(name=new_category)
                db.session.add(category)
                db.session.flush()  # Get the ID
                category_id = category.id

            # Check for duplicate SKU
            if sku:
                existing = InventoryItem.query.filter_by(sku=sku).first()
                if existing:
                    flash("SKU already exists", "error")
                    return redirect(url_for("inventory.add_item"))

            # Create new item
            item = InventoryItem(
                name=name,
                category_id=(
                    int(category_id) if category_id else 1
                ),  # Default category if none
                description=description,
                current_stock=int(current_stock),
                minimum_stock=int(minimum_stock),
                unit_of_measure=unit,
                cost_per_unit=unit_cost or 0.0,
                image_filename=image_filename,
            )
            if sku:
                item.barcode = sku

            db.session.add(item)
            db.session.commit()

            # Log initial stock if any
            if current_stock > 0:
                movement = StockMovement()
                movement.item_id = item.id
                movement.movement_type = "IN"
                movement.quantity = current_stock
                movement.reason = "Initial stock"
                movement.user_id = current_user.id

                db.session.add(movement)
                db.session.commit()

            flash("Item added successfully", "success")
            return redirect(url_for("inventory.list_items"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding item: {str(e)}", "error")
            return redirect(url_for("inventory.add_item"))

    # GET request - show form
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()
    return render_template("inventory/item_form.html", categories=categories)


@inventory.route("/items/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(id):
    """Edit an existing inventory item"""
    item = InventoryItem.query.get_or_404(id)

    if request.method == "POST":
        try:
            # Store original stock for movement tracking
            original_stock = item.current_stock

            # Get form data
            item.name = request.form.get("name", "").strip()
            item.sku = request.form.get("sku", "").strip() or None
            item.description = request.form.get("description", "").strip() or None
            category_id = request.form.get("category_id", type=int) or None
            new_category = request.form.get("new_category", "").strip()
            new_stock = request.form.get("current_stock", type=float) or 0
            item.minimum_stock = request.form.get("minimum_stock", type=float) or 0
            item.unit = request.form.get("unit", "").strip()
            item.cost_per_unit = request.form.get("unit_cost", type=float) or None

            # Handle image upload
            if "item_image" in request.files:
                file = request.files["item_image"]
                if file and file.filename:
                    # Delete old image if exists
                    if item.image_filename:
                        delete_image(item.image_filename)

                    # Save new image
                    new_image_filename = save_uploaded_image(file)
                    if new_image_filename:
                        item.image_filename = new_image_filename
                    else:
                        flash(
                            "Invalid image file. Please upload PNG, JPG, JPEG, GIF, or WebP files.",
                            "error",
                        )
                        return redirect(url_for("inventory.edit_item", id=id))

            # Validate required fields
            if not item.name:
                flash("Item name is required", "error")
                return redirect(url_for("inventory.edit_item", id=id))

            if not item.unit:
                flash("Unit is required", "error")
                return redirect(url_for("inventory.edit_item", id=id))

            # Handle new category creation
            if new_category and not category_id:
                category = InventoryCategory(name=new_category)
                db.session.add(category)
                db.session.flush()
                category_id = category.id

            item.category_id = category_id

            # Check for duplicate SKU (excluding current item)
            if item.sku:
                existing = InventoryItem.query.filter(
                    InventoryItem.sku == item.sku, InventoryItem.id != id
                ).first()
                if existing:
                    flash("SKU already exists", "error")
                    return redirect(url_for("inventory.edit_item", id=id))

            # Track stock changes
            if new_stock != original_stock:
                stock_diff = new_stock - original_stock
                movement_type = "IN" if stock_diff > 0 else "OUT"
                movement = StockMovement()
                movement.item_id = item.id
                movement.movement_type = movement_type
                movement.quantity = abs(stock_diff)
                movement.reason = "Stock adjustment via edit"
                movement.user_id = current_user.id

                db.session.add(movement)
                item.current_stock = new_stock

            db.session.commit()
            flash("Item updated successfully", "success")
            return redirect(url_for("inventory.list_items"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating item: {str(e)}", "error")

    # GET request - show form
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()
    return render_template("inventory/item_form.html", item=item, categories=categories)


@inventory.route("/items/<int:id>/update_stock", methods=["POST"])
@login_required
def update_stock(id):
    """Update stock for an item"""
    item = InventoryItem.query.get_or_404(id)

    try:
        movement_type = request.form.get("movement_type")
        quantity = request.form.get("quantity", type=float)
        reason = request.form.get("reason", "").strip() or None

        if not movement_type or not quantity or quantity <= 0:
            flash("Invalid movement data", "error")
            return redirect(url_for("inventory.list_items"))

        # Calculate new stock level
        if movement_type == "IN":
            new_stock = item.current_stock + quantity
        elif movement_type == "OUT":
            new_stock = max(
                0, item.current_stock - quantity
            )  # Don't allow negative stock
        else:  # ADJUSTMENT
            new_stock = quantity
            # For adjustments, recalculate quantity and type
            actual_quantity = abs(new_stock - item.current_stock)
            movement_type = "IN" if new_stock > item.current_stock else "OUT"
            quantity = actual_quantity

        # Create movement record
        movement = StockMovement()
        movement.item_id = item.id
        movement.movement_type = movement_type
        movement.quantity = quantity
        movement.reason = reason
        movement.user_id = current_user.id

        # Update item stock
        item.current_stock = new_stock

        db.session.add(movement)
        db.session.commit()

        # Check if stock is now low and create notifications
        try:
            from .models import User
            from .notifications import create_inventory_notification

            # Check if item is now low stock or out of stock
            if new_stock <= 0:
                # Out of stock - notify all users
                users = User.query.all()
                for user in users:
                    create_inventory_notification(user.id, item, "out_of_stock")
            elif new_stock <= item.minimum_stock:
                # Low stock - notify all users
                users = User.query.all()
                for user in users:
                    # Check if notification already exists in the last 24 hours
                    from datetime import datetime, timedelta

                    from .models import Notification

                    recent_notification = Notification.query.filter(
                        Notification.user_id == user.id,
                        Notification.related_model == "inventory",
                        Notification.related_id == str(item.id),
                        Notification.notification_type.in_(["warning", "error"]),
                        Notification.created_at
                        >= datetime.utcnow() - timedelta(hours=24),
                    ).first()

                    if not recent_notification:
                        create_inventory_notification(user.id, item, "low_stock")
        except Exception as e:
            print(f"Failed to create inventory notification: {e}")

        flash("Stock updated successfully", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating stock: {str(e)}", "error")

    return redirect(url_for("inventory.list_items"))


@inventory.route("/items/<int:id>/delete", methods=["POST"])
@login_required
def delete_item(id):
    """Delete an inventory item"""
    item = InventoryItem.query.get_or_404(id)

    try:
        # Delete related stock movements
        StockMovement.query.filter_by(item_id=id).delete()

        # Delete the item
        db.session.delete(item)
        db.session.commit()

        flash("Item deleted successfully", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", "error")

    return redirect(url_for("inventory.list_items"))


@inventory.route("/movements")
@login_required
def stock_movements():
    """List all stock movements with filtering"""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    movement_type = request.args.get("movement_type", "").strip()
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    # Base query
    query = StockMovement.query.join(InventoryItem)

    # Apply filters
    if search:
        query = query.filter(
            or_(
                InventoryItem.name.ilike(f"%{search}%"),
                StockMovement.reason.ilike(f"%{search}%"),
            )
        )

    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
            query = query.filter(func.date(StockMovement.created_at) >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
            query = query.filter(func.date(StockMovement.created_at) <= date_to_obj)
        except ValueError:
            pass

    # Get paginated results
    movements = query.order_by(desc(StockMovement.created_at)).paginate(
        page=page, per_page=50, error_out=False
    )

    # Get summary statistics
    today = date.today()
    today_in = StockMovement.query.filter(
        StockMovement.movement_type == "IN",
        func.date(StockMovement.created_at) == today,
    ).count()

    today_out = StockMovement.query.filter(
        StockMovement.movement_type == "OUT",
        func.date(StockMovement.created_at) == today,
    ).count()

    total_movements = StockMovement.query.count()

    return render_template(
        "inventory/movements.html",
        movements=movements,
        today_in=today_in,
        today_out=today_out,
        total_movements=total_movements,
    )


@inventory.route("/reports")
@login_required
def reports():
    """Generate inventory reports"""
    report_type = request.args.get("report_type")
    report_data = None
    report_summary = {}
    report_title = ""

    if report_type:
        if report_type == "stock_levels":
            # Stock levels report
            category_id = request.args.get("category_id", type=int)
            query = InventoryItem.query
            if category_id:
                query = query.filter(InventoryItem.category_id == category_id)  # type: ignore
            report_data = query.order_by(InventoryItem.name).all()
            report_title = "Stock Level Report"

        elif report_type == "stock_movements":
            # Stock movements report
            date_from = request.args.get("date_from")
            date_to = request.args.get("date_to")

            query = StockMovement.query
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, "%Y-%m-%d").date()
                    query = query.filter(
                        func.date(StockMovement.created_at) >= date_from_obj
                    )
                except ValueError:
                    pass

            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, "%Y-%m-%d").date()
                    query = query.filter(
                        func.date(StockMovement.created_at) <= date_to_obj
                    )
                except ValueError:
                    pass

            report_data = query.order_by(desc(StockMovement.created_at)).all()

            # Calculate summary
            total_in = sum(m.quantity for m in report_data if m.movement_type == "IN")
            total_out = sum(m.quantity for m in report_data if m.movement_type == "OUT")
            report_summary = {"total_in": total_in, "total_out": total_out}
            report_title = "Stock Movement Report"

        elif report_type == "low_stock":
            # Low stock report
            report_data = (
                InventoryItem.query.filter(
                    InventoryItem.current_stock <= InventoryItem.minimum_stock  # type: ignore
                )
                .order_by(InventoryItem.name)
                .all()
            )
            report_title = "Low Stock Alert Report"

        elif report_type == "inventory_value":
            # Inventory value report
            items = InventoryItem.query.all()
            total_value = sum(
                (item.cost_per_unit or 0) * item.current_stock for item in items
            )

            # Value by category
            categories = InventoryCategory.query.all()
            category_values = []
            for category in categories:
                cat_value = sum(
                    (item.cost_per_unit or 0) * item.current_stock
                    for item in category.items
                )
                if cat_value > 0:
                    category_values.append({"name": category.name, "value": cat_value})

            # Top valuable items
            top_items = sorted(
                items,
                key=lambda x: (x.cost_per_unit or 0) * x.current_stock,
                reverse=True,
            )[:10]

            report_summary = {
                "total_value": total_value,
                "category_values": category_values,
                "top_items": top_items,
            }
            report_title = "Inventory Value Report"

    # Get categories for filters
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()

    return render_template(
        "inventory/reports.html",
        categories=categories,
        report_data=report_data,
        report_summary=report_summary,
        report_title=report_title,
    )


@inventory.route("/summary")
@login_required
def summary():
    """Summary view for inventory IN and OUT totals and top items

    Supports query parameters:
      - period: 'today', '7', '30', 'all' (default 7)
      - page: pagination page for top lists (default 1)
      - per_page: number of items per page for top lists (default 10)
      - category: optional category name to filter by
    """
    period = request.args.get("period", "7")  # 'today', '7', '30', 'all'
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    category = request.args.get("category", None)

    # Determine date range
    if period == "today":
        start = datetime.combine(date.today(), datetime.min.time())
    elif period == "all":
        start = None
    else:
        try:
            days = int(period)
            start = datetime.utcnow() - timedelta(days=days)
        except Exception:
            start = datetime.utcnow() - timedelta(days=7)

    # Totals
    in_q = db.session.query(func.coalesce(func.sum(StockMovement.quantity), 0)).filter(StockMovement.movement_type == "IN")
    out_q = db.session.query(func.coalesce(func.sum(StockMovement.quantity), 0)).filter(StockMovement.movement_type == "OUT")

    if start:
        in_q = in_q.filter(StockMovement.created_at >= start)
        out_q = out_q.filter(StockMovement.created_at >= start)

    if category:
        in_q = in_q.join(InventoryItem).filter(InventoryItem.category.has(name=category))
        out_q = out_q.join(InventoryItem).filter(InventoryItem.category.has(name=category))

    total_in = int(in_q.scalar() or 0)
    total_out = int(out_q.scalar() or 0)

    # Top items (by quantity) for IN and OUT with pagination
    in_query = db.session.query(
        InventoryItem.id,
        InventoryItem.name,
        func.coalesce(func.sum(StockMovement.quantity), 0).label("total_in"),
    ).join(StockMovement).filter(StockMovement.movement_type == "IN")

    out_query = db.session.query(
        InventoryItem.id,
        InventoryItem.name,
        func.coalesce(func.sum(StockMovement.quantity), 0).label("total_out"),
    ).join(StockMovement).filter(StockMovement.movement_type == "OUT")

    if start:
        in_query = in_query.filter(StockMovement.created_at >= start)
        out_query = out_query.filter(StockMovement.created_at >= start)

    if category:
        in_query = in_query.filter(InventoryItem.category.has(name=category))
        out_query = out_query.filter(InventoryItem.category.has(name=category))

    in_query = in_query.group_by(InventoryItem.id).order_by(desc("total_in"))
    out_query = out_query.group_by(InventoryItem.id).order_by(desc("total_out"))

    top_in = in_query.limit(per_page).offset((page - 1) * per_page).all()
    top_out = out_query.limit(per_page).offset((page - 1) * per_page).all()

    # Inventory items table (paginated)
    items_page_num = request.args.get('items_page', 1, type=int)
    items_per_page = request.args.get('items_per_page', 20, type=int)

    items_query = InventoryItem.query
    if category:
        items_query = items_query.filter(InventoryItem.category.has(name=category))

    items_pagination = items_query.order_by(InventoryItem.name).paginate(page=items_page_num, per_page=items_per_page, error_out=False)

    return render_template(
        "inventory/summary.html",
        period=period,
        total_in=total_in,
        total_out=total_out,
        top_in=top_in,
        top_out=top_out,
        page=page,
        per_page=per_page,
        category=category,
        categories=InventoryCategory.query.order_by(InventoryCategory.name).all(),
        items_page=items_pagination,
    )


@inventory.route("/summary/export.csv")
@login_required
def summary_export_csv():
    """Export stock movements for the selected period/category as CSV"""
    period = request.args.get("period", "7")
    category = request.args.get("category", None)

    # Determine start date
    if period == "today":
        start = datetime.combine(date.today(), datetime.min.time())
    elif period == "all":
        start = None
    else:
        try:
            days = int(period)
            start = datetime.utcnow() - timedelta(days=days)
        except Exception:
            start = datetime.utcnow() - timedelta(days=7)

    q = db.session.query(StockMovement, InventoryItem.name.label("item_name"), InventoryItem.id.label("item_id"))\
        .join(InventoryItem, StockMovement.item_id == InventoryItem.id).order_by(desc(StockMovement.created_at))

    if start:
        q = q.filter(StockMovement.created_at >= start)

    if category:
        q = q.filter(InventoryItem.category.has(name=category))

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["movement_id", "item_id", "item_name", "movement_type", "quantity", "stock_before", "stock_after", "created_at", "reference_type", "reference_id", "notes"]) 

    for m, item_name, item_id in q.all():
        created_at = m.created_at.isoformat() if m.created_at else ""
        writer.writerow([m.id, item_id, item_name, m.movement_type, m.quantity, m.stock_before, m.stock_after, created_at, m.reference_type, m.reference_id, m.notes or ""])

    output = BytesIO()
    output.write(si.getvalue().encode("utf-8"))
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="inventory_summary.csv",
        mimetype="text/csv",
    )
