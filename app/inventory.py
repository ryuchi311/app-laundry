from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import InventoryItem, InventoryCategory, StockMovement, User
from . import db
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc, asc, or_

inventory = Blueprint('inventory', __name__)

@inventory.route('/dashboard')
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
    recent_movements = StockMovement.query.order_by(desc(StockMovement.created_at)).limit(10).all()
    
    # Get categories for overview
    categories = InventoryCategory.query.all()
    
    return render_template('inventory/dashboard.html',
                         total_items=total_items,
                         total_categories=total_categories,
                         total_value=total_value,
                         low_stock_count=low_stock_count,
                         low_stock_items=low_stock_items,
                         recent_movements=recent_movements,
                         categories=categories)

@inventory.route('/items')
@login_required
def list_items():
    """List all inventory items with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)
    status_filter = request.args.get('status', '').strip()
    
    # Base query
    query = InventoryItem.query
    
    # Apply search filter
    if search:
        query = query.filter(or_(
            InventoryItem.name.ilike(f'%{search}%'),
            InventoryItem.sku.ilike(f'%{search}%'),
            InventoryItem.description.ilike(f'%{search}%')
        ))
    
    # Apply category filter
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)  # type: ignore
    
    # Apply status filter
    if status_filter:
        if status_filter == 'low_stock':
            query = query.filter(InventoryItem.current_stock <= InventoryItem.minimum_stock)  # type: ignore
        elif status_filter == 'out_of_stock':
            query = query.filter(InventoryItem.current_stock <= 0)  # type: ignore
        elif status_filter == 'in_stock':
            query = query.filter(InventoryItem.current_stock > InventoryItem.minimum_stock)  # type: ignore
    
    # Paginate results
    items = query.order_by(InventoryItem.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories for filter dropdown
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()
    
    return render_template('inventory/items.html', items=items, categories=categories)

@inventory.route('/items/add', methods=['GET', 'POST'])
@login_required
def add_item():
    """Add a new inventory item"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            sku = request.form.get('sku', '').strip() or None
            description = request.form.get('description', '').strip() or None
            category_id = request.form.get('category_id', type=int) or None
            new_category = request.form.get('new_category', '').strip()
            current_stock = request.form.get('current_stock', type=float) or 0
            minimum_stock = request.form.get('minimum_stock', type=float) or 0
            unit = request.form.get('unit', '').strip()
            unit_cost = request.form.get('unit_cost', type=float) or None
            
            # Validate required fields
            if not name:
                flash('Item name is required', 'error')
                return redirect(url_for('inventory.add_item'))
            
            if not unit:
                flash('Unit is required', 'error')
                return redirect(url_for('inventory.add_item'))
            
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
                    flash('SKU already exists', 'error')
                    return redirect(url_for('inventory.add_item'))
            
            # Create new item
            item = InventoryItem(
                name=name,
                category_id=int(category_id) if category_id else 1,  # Default category if none
                description=description,
                current_stock=int(current_stock),
                minimum_stock=int(minimum_stock),
                unit_of_measure=unit,
                cost_per_unit=unit_cost or 0.0
            )
            if sku:
                item.barcode = sku
            
            db.session.add(item)
            db.session.commit()
            
            # Log initial stock if any
            if current_stock > 0:
                movement = StockMovement()
                movement.item_id = item.id
                movement.movement_type = 'IN'
                movement.quantity = current_stock
                movement.reason = 'Initial stock'
                movement.user_id = current_user.id
                
                db.session.add(movement)
                db.session.commit()
            
            flash('Item added successfully', 'success')
            return redirect(url_for('inventory.list_items'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', 'error')
            return redirect(url_for('inventory.add_item'))
    
    # GET request - show form
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()
    return render_template('inventory/item_form.html', categories=categories)

@inventory.route('/items/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    """Edit an existing inventory item"""
    item = InventoryItem.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Store original stock for movement tracking
            original_stock = item.current_stock
            
            # Get form data
            item.name = request.form.get('name', '').strip()
            item.sku = request.form.get('sku', '').strip() or None
            item.description = request.form.get('description', '').strip() or None
            category_id = request.form.get('category_id', type=int) or None
            new_category = request.form.get('new_category', '').strip()
            new_stock = request.form.get('current_stock', type=float) or 0
            item.minimum_stock = request.form.get('minimum_stock', type=float) or 0
            item.unit = request.form.get('unit', '').strip()
            item.cost_per_unit = request.form.get('unit_cost', type=float) or None
            
            # Validate required fields
            if not item.name:
                flash('Item name is required', 'error')
                return redirect(url_for('inventory.edit_item', id=id))
            
            if not item.unit:
                flash('Unit is required', 'error')
                return redirect(url_for('inventory.edit_item', id=id))
            
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
                    InventoryItem.sku == item.sku,
                    InventoryItem.id != id
                ).first()
                if existing:
                    flash('SKU already exists', 'error')
                    return redirect(url_for('inventory.edit_item', id=id))
            
            # Track stock changes
            if new_stock != original_stock:
                stock_diff = new_stock - original_stock
                movement_type = 'IN' if stock_diff > 0 else 'OUT'
                movement = StockMovement()
                movement.item_id = item.id
                movement.movement_type = movement_type
                movement.quantity = abs(stock_diff)
                movement.reason = f'Stock adjustment via edit'
                movement.user_id = current_user.id
                
                db.session.add(movement)
                item.current_stock = new_stock
            
            db.session.commit()
            flash('Item updated successfully', 'success')
            return redirect(url_for('inventory.list_items'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating item: {str(e)}', 'error')
    
    # GET request - show form
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()
    return render_template('inventory/item_form.html', item=item, categories=categories)

@inventory.route('/items/<int:id>/update_stock', methods=['POST'])
@login_required
def update_stock(id):
    """Update stock for an item"""
    item = InventoryItem.query.get_or_404(id)
    
    try:
        movement_type = request.form.get('movement_type')
        quantity = request.form.get('quantity', type=float)
        reason = request.form.get('reason', '').strip() or None
        
        if not movement_type or not quantity or quantity <= 0:
            flash('Invalid movement data', 'error')
            return redirect(url_for('inventory.list_items'))
        
        # Calculate new stock level
        if movement_type == 'IN':
            new_stock = item.current_stock + quantity
        elif movement_type == 'OUT':
            new_stock = max(0, item.current_stock - quantity)  # Don't allow negative stock
        else:  # ADJUSTMENT
            new_stock = quantity
            # For adjustments, recalculate quantity and type
            actual_quantity = abs(new_stock - item.current_stock)
            movement_type = 'IN' if new_stock > item.current_stock else 'OUT'
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
            from .notifications import create_inventory_notification
            from .models import User
            
            # Check if item is now low stock or out of stock
            if new_stock <= 0:
                # Out of stock - notify all users
                users = User.query.all()
                for user in users:
                    create_inventory_notification(user.id, item, 'out_of_stock')
            elif new_stock <= item.minimum_stock:
                # Low stock - notify all users
                users = User.query.all()
                for user in users:
                    # Check if notification already exists in the last 24 hours
                    from datetime import datetime, timedelta
                    from .models import Notification
                    recent_notification = Notification.query.filter(
                        Notification.user_id == user.id,
                        Notification.related_model == 'inventory',
                        Notification.related_id == str(item.id),
                        Notification.notification_type.in_(['warning', 'error']),
                        Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
                    ).first()
                    
                    if not recent_notification:
                        create_inventory_notification(user.id, item, 'low_stock')
        except Exception as e:
            print(f"Failed to create inventory notification: {e}")
        
        flash('Stock updated successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating stock: {str(e)}', 'error')
    
    return redirect(url_for('inventory.list_items'))

@inventory.route('/items/<int:id>/delete', methods=['POST'])
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
        
        flash('Item deleted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'error')
    
    return redirect(url_for('inventory.list_items'))

@inventory.route('/movements')
@login_required
def stock_movements():
    """List all stock movements with filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    movement_type = request.args.get('movement_type', '').strip()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Base query
    query = StockMovement.query.join(InventoryItem)
    
    # Apply filters
    if search:
        query = query.filter(or_(
            InventoryItem.name.ilike(f'%{search}%'),
            StockMovement.reason.ilike(f'%{search}%')
        ))
    
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(func.date(StockMovement.created_at) >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
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
        StockMovement.movement_type == 'IN',
        func.date(StockMovement.created_at) == today
    ).count()
    
    today_out = StockMovement.query.filter(
        StockMovement.movement_type == 'OUT',
        func.date(StockMovement.created_at) == today
    ).count()
    
    total_movements = StockMovement.query.count()
    
    return render_template('inventory/movements.html',
                         movements=movements,
                         today_in=today_in,
                         today_out=today_out,
                         total_movements=total_movements)

@inventory.route('/reports')
@login_required
def reports():
    """Generate inventory reports"""
    report_type = request.args.get('report_type')
    report_data = None
    report_summary = {}
    report_title = ""
    
    if report_type:
        if report_type == 'stock_levels':
            # Stock levels report
            category_id = request.args.get('category_id', type=int)
            query = InventoryItem.query
            if category_id:
                query = query.filter(InventoryItem.category_id == category_id)  # type: ignore
            report_data = query.order_by(InventoryItem.name).all()
            report_title = "Stock Level Report"
            
        elif report_type == 'stock_movements':
            # Stock movements report
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            
            query = StockMovement.query
            if date_from:
                try:
                    date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
                    query = query.filter(func.date(StockMovement.created_at) >= date_from_obj)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
                    query = query.filter(func.date(StockMovement.created_at) <= date_to_obj)
                except ValueError:
                    pass
            
            report_data = query.order_by(desc(StockMovement.created_at)).all()
            
            # Calculate summary
            total_in = sum(m.quantity for m in report_data if m.movement_type == 'IN')
            total_out = sum(m.quantity for m in report_data if m.movement_type == 'OUT')
            report_summary = {'total_in': total_in, 'total_out': total_out}
            report_title = "Stock Movement Report"
            
        elif report_type == 'low_stock':
            # Low stock report
            report_data = InventoryItem.query.filter(
                InventoryItem.current_stock <= InventoryItem.minimum_stock  # type: ignore
            ).order_by(InventoryItem.name).all()
            report_title = "Low Stock Alert Report"
            
        elif report_type == 'inventory_value':
            # Inventory value report
            items = InventoryItem.query.all()
            total_value = sum((item.cost_per_unit or 0) * item.current_stock for item in items)
            
            # Value by category
            categories = InventoryCategory.query.all()
            category_values = []
            for category in categories:
                cat_value = sum((item.cost_per_unit or 0) * item.current_stock 
                              for item in category.items)
                if cat_value > 0:
                    category_values.append({'name': category.name, 'value': cat_value})
            
            # Top valuable items
            top_items = sorted(items, 
                             key=lambda x: (x.cost_per_unit or 0) * x.current_stock, 
                             reverse=True)[:10]
            
            report_summary = {
                'total_value': total_value,
                'category_values': category_values,
                'top_items': top_items
            }
            report_title = "Inventory Value Report"
    
    # Get categories for filters
    categories = InventoryCategory.query.order_by(InventoryCategory.name).all()
    
    return render_template('inventory/reports.html',
                         categories=categories,
                         report_data=report_data,
                         report_summary=report_summary,
                         report_title=report_title)
