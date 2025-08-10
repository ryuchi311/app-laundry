from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Customer, Laundry, Service, Expense, InventoryItem, DashboardWidget
from .sms_service import sms_service
from . import db
from sqlalchemy import func, desc
from datetime import datetime
import os

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def dashboard():
    # Get user's customized dashboard widgets
    user_widgets = get_user_dashboard_config(current_user.id)
    
    total_customers = Customer.query.count()
    active_laundries = Laundry.query.filter(Laundry.status != 'Completed').count()
    completed_laundries = Laundry.query.filter_by(status='Completed').count()
    
    # Calculate real revenue from completed laundries
    total_revenue = db.session.query(func.sum(Laundry.price)).filter_by(status='Completed').scalar() or 0
    
    # Calculate estimated revenue from active laundries
    estimated_revenue = db.session.query(func.sum(Laundry.price)).filter(Laundry.status != 'Completed').scalar() or 0
    
    # Service statistics
    total_services = Service.query.count()
    active_services = Service.query.filter_by(is_active=True).count()
    
    # Get popular services (top 3 by laundry count)
    popular_services = db.session.query(
        Service.name, 
        Service.icon,
        Service.category,
        func.count(Laundry.id).label('laundry_count')
    ).join(Laundry, Laundry.service_id == Service.id, isouter=True)\
     .group_by(Service.id)\
     .order_by(func.count(Laundry.id).desc())\
     .limit(3).all()
    
    # Get all active services for pricing display
    all_services = Service.query.filter_by(is_active=True).order_by(Service.category, Service.name).all()
    
    # Get recent laundry orders (last 5)
    recent_laundries = Laundry.query.order_by(desc(Laundry.date_received)).limit(5).all()
    
    # Get recent expenses (last 5)
    recent_expenses = Expense.query.order_by(desc(Expense.expense_date)).limit(5).all()
    
    # Get inventory statistics
    total_inventory_items = InventoryItem.query.filter_by(is_active=True).count()
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.minimum_stock,  # type: ignore
        InventoryItem.is_active == True  # type: ignore
    ).all()
    out_of_stock_items = InventoryItem.query.filter(
        InventoryItem.current_stock <= 0,  # type: ignore
        InventoryItem.is_active == True  # type: ignore
    ).all()
    
    # Calculate total inventory value
    total_inventory_value = db.session.query(
        func.sum(InventoryItem.current_stock * InventoryItem.cost_per_unit)
    ).filter(InventoryItem.is_active == True).scalar() or 0  # type: ignore

    return render_template("dashboard.html", 
                         user=current_user,
                         total_customers=total_customers,
                         active_laundries=active_laundries,
                         completed_laundries=completed_laundries,
                         total_revenue=total_revenue,
                         estimated_revenue=estimated_revenue,
                         total_services=total_services,
                         active_services=active_services,
                         popular_services=popular_services,
                         all_services=all_services,
                         recent_laundries=recent_laundries,
                         recent_expenses=recent_expenses,
                         total_inventory_items=total_inventory_items,
                         low_stock_items=low_stock_items,
                         out_of_stock_items=out_of_stock_items,
                         total_inventory_value=total_inventory_value,
                         user_widgets=user_widgets)

# Dashboard Customization Routes
def get_default_widgets():
    """Get the default dashboard widgets configuration"""
    return [
        {'id': 'stats_overview', 'name': 'Statistics Overview', 'position': 0, 'size': 'large'},
        {'id': 'recent_orders', 'name': 'Recent Laundry Orders', 'position': 1, 'size': 'normal'},
        {'id': 'inventory_status', 'name': 'Inventory Status', 'position': 2, 'size': 'normal'},
        {'id': 'revenue_chart', 'name': 'Revenue Overview', 'position': 3, 'size': 'normal'},
        {'id': 'low_stock_alerts', 'name': 'Low Stock Alerts', 'position': 4, 'size': 'normal'},
        {'id': 'popular_services', 'name': 'Popular Services', 'position': 5, 'size': 'small'},
        {'id': 'recent_expenses', 'name': 'Recent Expenses', 'position': 6, 'size': 'small'},
        {'id': 'quick_actions', 'name': 'Quick Actions', 'position': 7, 'size': 'small'},
    ]

def get_user_dashboard_config(user_id):
    """Get user's dashboard configuration or create default"""
    widgets = DashboardWidget.query.filter_by(user_id=user_id).order_by(DashboardWidget.position).all()  # type: ignore
    
    if not widgets:
        # Create default configuration for new user
        default_widgets = get_default_widgets()
        for widget_config in default_widgets:
            widget = DashboardWidget(
                user_id=user_id,
                widget_id=widget_config['id'],
                position=widget_config['position'],
                widget_size=widget_config['size']
            )
            db.session.add(widget)
        db.session.commit()
        
        # Re-fetch the newly created widgets
        widgets = DashboardWidget.query.filter_by(user_id=user_id).order_by(DashboardWidget.position).all()  # type: ignore
    
    return widgets

@views.route('/dashboard/customize')
@login_required
def customize_dashboard():
    """Show dashboard customization interface"""
    widgets = get_user_dashboard_config(current_user.id)
    default_widgets = get_default_widgets()
    
    # Merge with default widget names
    widget_configs = []
    for widget in widgets:
        default_config = next((w for w in default_widgets if w['id'] == widget.widget_id), {})
        widget_configs.append({
            'id': widget.widget_id,
            'name': default_config.get('name', widget.widget_id.replace('_', ' ').title()),
            'position': widget.position,
            'is_visible': widget.is_visible,
            'size': widget.widget_size
        })
    
    return render_template('dashboard_customize.html', widgets=widget_configs)

@views.route('/dashboard/api/save-layout', methods=['POST'])
@login_required
def save_dashboard_layout():
    """Save dashboard layout changes"""
    try:
        data = request.get_json()
        widgets_data = data.get('widgets', [])
        
        # Update widget positions and visibility
        for widget_data in widgets_data:
            widget = DashboardWidget.query.filter_by(
                user_id=current_user.id, 
                widget_id=widget_data['id']
            ).first()
            
            if widget:
                widget.position = widget_data.get('position', widget.position)
                widget.is_visible = widget_data.get('is_visible', widget.is_visible)
                widget.widget_size = widget_data.get('size', widget.widget_size)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Dashboard layout saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving layout: {str(e)}'})

@views.route('/dashboard/api/reset-layout', methods=['POST'])
@login_required
def reset_dashboard_layout():
    """Reset dashboard to default layout"""
    try:
        # Delete existing widgets
        DashboardWidget.query.filter_by(user_id=current_user.id).delete()
        
        # Recreate default widgets
        default_widgets = get_default_widgets()
        for widget_config in default_widgets:
            widget = DashboardWidget(
                user_id=current_user.id,
                widget_id=widget_config['id'],
                position=widget_config['position'],
                widget_size=widget_config['size']
            )
            db.session.add(widget)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Dashboard reset to default layout'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error resetting layout: {str(e)}'})

@views.route('/dashboard/api/auto-organize', methods=['POST'])
@login_required
def auto_organize_dashboard():
    """Auto-organize dashboard widgets by priority/usage"""
    try:
        data = request.get_json()
        organize_by = data.get('method', 'priority')  # 'priority', 'usage', 'size'
        
        widgets = DashboardWidget.query.filter_by(user_id=current_user.id).all()
        
        if organize_by == 'priority':
            # Organize by predefined priority
            priority_order = {
                'stats_overview': 0,
                'recent_orders': 1,
                'inventory_status': 2,
                'low_stock_alerts': 3,
                'revenue_chart': 4,
                'popular_services': 5,
                'recent_expenses': 6,
                'quick_actions': 7
            }
            
            for widget in widgets:
                widget.position = priority_order.get(widget.widget_id, 99)
                
        elif organize_by == 'size':
            # Organize by size (large first, then normal, then small)
            size_priority = {'large': 0, 'normal': 1, 'small': 2}
            
            sorted_widgets = sorted(widgets, key=lambda w: (size_priority.get(w.widget_size, 3), w.widget_id))
            for i, widget in enumerate(sorted_widgets):
                widget.position = i
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'Dashboard organized by {organize_by}'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error organizing dashboard: {str(e)}'})

@views.route('/dashboard/api/toggle-widget', methods=['POST'])
@login_required  
def toggle_widget_visibility():
    """Toggle widget visibility"""
    try:
        data = request.get_json()
        widget_id = data.get('widget_id')
        
        widget = DashboardWidget.query.filter_by(
            user_id=current_user.id,
            widget_id=widget_id
        ).first()
        
        if widget:
            widget.is_visible = not widget.is_visible
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Widget {"shown" if widget.is_visible else "hidden"}',
                'is_visible': widget.is_visible
            })
        else:
            return jsonify({'success': False, 'message': 'Widget not found'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error toggling widget: {str(e)}'})

@views.route('/dashboard/save-widgets', methods=['POST'])
@login_required
def save_live_dashboard_layout():
    """Save dashboard widget layout and visibility for live editing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No layout data provided'})
        
        # Update each widget's position and visibility
        for widget_id, settings in data.items():
            widget = DashboardWidget.query.filter_by(
                user_id=current_user.id,
                widget_id=widget_id
            ).first()
            
            if widget:
                if 'position' in settings:
                    widget.position = settings['position']
                if 'visible' in settings:
                    widget.is_visible = settings['visible']
                widget.updated_at = datetime.utcnow()
            else:
                # Create new widget if it doesn't exist
                widget = DashboardWidget(
                    user_id=current_user.id,
                    widget_id=widget_id,
                    position=settings.get('position', 0),
                    is_visible=settings.get('visible', True)
                )
                db.session.add(widget)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Dashboard layout saved successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving layout: {str(e)}'})