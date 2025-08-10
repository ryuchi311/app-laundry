from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Customer, Laundry, Service, Expense, InventoryItem, DashboardWidget
from .decorators import admin_required
from .sms_service import sms_service
from . import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import os
import json

views = Blueprint('views', __name__)


def get_default_widgets(role):
    """Get default widgets based on user role"""
    if role == 'super_admin':
        # Super Admin: Full system access including financial, user management, and system settings
        return ['total_customers', 'active_laundries', 'completed_laundries', 'total_revenue', 'estimated_revenue', 'total_services', 'recent_expenses', 'inventory_alerts', 'user_management']
    elif role == 'admin':
        # Admin: Full operational access including financial reports
        return ['total_customers', 'active_laundries', 'completed_laundries', 'total_revenue', 'estimated_revenue', 'total_services', 'recent_expenses', 'inventory_alerts']
    elif role == 'manager':
        # Manager: Operational oversight with limited financial access
        return ['total_customers', 'active_laundries', 'completed_laundries', 'total_revenue', 'total_services', 'inventory_alerts', 'service_performance']
    else:  # Employee
        # Employee: Basic operational access
        return ['active_laundries', 'completed_laundries', 'total_services', 'my_tasks']


def get_role_based_widgets(user_id):
    """Get user's widget configuration based on their role and preferences"""
    user = current_user
    
    # Get user's custom widgets or default based on role
    custom_widgets = DashboardWidget.query.filter_by(user_id=user_id, is_visible=True).all()
    
    if custom_widgets:
        # Return user's custom widget configuration
        return [w.widget_id for w in sorted(custom_widgets, key=lambda x: x.position or 0)]
    else:
        # Return default widgets for user's role
        return get_default_widgets(user.role)


def get_user_dashboard_config(user_id):
    """Get user's dashboard widget configuration"""
    return get_role_based_widgets(user_id)


@views.route('/')
@login_required
def dashboard():
    # Get user's customized dashboard widgets based on role
    user_widgets = get_user_dashboard_config(current_user.id)
    
    # Initialize dashboard data dictionary
    dashboard_data = {}
    
    # Common data for all users
    active_laundries = Laundry.query.filter(Laundry.status != 'Completed').count()
    completed_laundries = Laundry.query.filter_by(status='Completed').count()
    total_services = Service.query.filter_by(is_active=True).count()
    active_services = Service.query.filter_by(is_active=True).count()
    
    # Recent laundries (last 10) - available to all users
    recent_laundries = Laundry.query.order_by(Laundry.date_received.desc()).limit(10).all()
    
    # Add common data to dashboard_data
    dashboard_data.update({
        'active_laundries': active_laundries,
        'completed_laundries': completed_laundries,
        'total_services': total_services,
        'active_services': active_services,
        'recent_laundries': recent_laundries,
    })
    
    # Role-based data access
    if current_user.is_admin():
        # Full admin access - all data including financial and system info
        total_customers = Customer.query.count()
        total_revenue = db.session.query(func.sum(Laundry.price)).filter(
            Laundry.status == 'Completed'
        ).scalar() or 0
        estimated_revenue = db.session.query(func.sum(Laundry.price)).filter(
            Laundry.status != 'Completed'
        ).scalar() or 0
        
        # Popular services (admin only)
        popular_services = db.session.query(
            Service.name,
            func.count(Laundry.id).label('count')
        ).join(Service.laundries).group_by(Service.id).order_by(desc('count')).limit(5).all()
        
        # Recent expenses (admin only)
        recent_expenses = Expense.query.order_by(Expense.expense_date.desc()).limit(5).all()
        
        # Add admin-specific data
        dashboard_data.update({
            'total_customers': total_customers,
            'total_revenue': total_revenue,
            'estimated_revenue': estimated_revenue,
            'popular_services': popular_services,
            'recent_expenses': recent_expenses,
        })
    elif current_user.is_manager():
        # Manager access - operational data and reports but limited financial access
        total_customers = Customer.query.count()
        total_revenue = db.session.query(func.sum(Laundry.price)).filter(
            Laundry.status == 'Completed'
        ).scalar() or 0
        estimated_revenue = db.session.query(func.sum(Laundry.price)).filter(
            Laundry.status != 'Completed'
        ).scalar() or 0
        
        # Popular services (manager access)
        popular_services = db.session.query(
            Service.name,
            func.count(Laundry.id).label('count')
        ).join(Service.laundries).group_by(Service.id).order_by(desc('count')).limit(5).all()
        
        # Recent expenses limited for managers (no sensitive financial data)
        recent_expenses = []
        
        # Add manager-specific data
        dashboard_data.update({
            'total_customers': total_customers,
            'total_revenue': total_revenue,
            'estimated_revenue': estimated_revenue,
            'popular_services': popular_services,
            'recent_expenses': recent_expenses,
        })
    else:
        # Employee access - basic operational data only
        dashboard_data.update({
            'total_customers': 0,
            'total_revenue': 0,
            'estimated_revenue': 0,
            'popular_services': [],
            'recent_expenses': [],
        })

    # Get all active services for pricing display (available to all users)
    all_services = Service.query.filter_by(is_active=True).order_by(Service.category, Service.name).all()
    dashboard_data['all_services'] = all_services
    
    # Admin-only statistics and charts
    if current_user.is_admin():
        # Get inventory statistics (admin only)
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

        # Additional stats for charts
        pending_laundries = Laundry.query.filter_by(status='Pending').count()
        in_progress_laundries = Laundry.query.filter_by(status='In Progress').count()
        picked_up_laundries = Laundry.query.filter_by(status='Picked Up').count()
        
        # Service type counts
        wash_only_services = Service.query.filter(Service.category == 'Standard').count()
        dry_only_services = Service.query.filter(Service.category == 'Express').count()
        wash_dry_services = Service.query.filter(Service.category == 'Premium').count()
        
        # Add admin-specific data to dashboard_data
        dashboard_data.update({
            'total_inventory_items': total_inventory_items,
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'total_inventory_value': total_inventory_value,
            'pending_laundries': pending_laundries,
            'in_progress_laundries': in_progress_laundries,
            'picked_up_laundries': picked_up_laundries,
        })
        
        # Prepare chart data as clean JSON objects (admin only)
        chart_data = {
            'revenue': {
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'data': [
                    round(dashboard_data['total_revenue'] * 0.6, 2), 
                    round(dashboard_data['total_revenue'] * 0.7, 2), 
                    round(dashboard_data['total_revenue'] * 0.8, 2), 
                    round(dashboard_data['total_revenue'] * 0.9, 2), 
                    round(dashboard_data['total_revenue'] * 0.95, 2), 
                    round(dashboard_data['total_revenue'], 2)
                ]
            },
            'services': {
                'labels': ['Standard', 'Express', 'Premium', 'Other'],
                'data': [
                    wash_only_services, 
                    dry_only_services, 
                    wash_dry_services, 
                    max(0, dashboard_data['total_services'] - (wash_only_services + dry_only_services + wash_dry_services))
                ]
            },
            'status': {
                'labels': ['Pending', 'In Progress', 'Completed', 'Picked Up'],
                'data': [pending_laundries, in_progress_laundries, dashboard_data['completed_laundries'], picked_up_laundries]
            },
            'inventory': {
                'labels': ['Total Items', 'Low Stock', 'Out of Stock', 'Healthy Stock'],
                'data': [
                    total_inventory_items, 
                    len(low_stock_items), 
                    len(out_of_stock_items), 
                    max(0, total_inventory_items - len(low_stock_items) - len(out_of_stock_items))
                ]
            }
        }
        dashboard_data['chart_data'] = chart_data
    else:
        # Regular users get simplified chart data
        dashboard_data.update({
            'total_inventory_items': 0,
            'low_stock_items': [],
            'out_of_stock_items': [],
            'total_inventory_value': 0,
            'chart_data': {}
        })

    # Prepare template data based on role
    template_data = {
        'user': current_user,
        'user_widgets': user_widgets,
        **dashboard_data  # Unpack all dashboard data
    }

    return render_template("dashboard.html", **template_data)


@views.route('/charts')
@login_required
def charts():
    """Interactive Charts page"""
    # Get the same data as dashboard for charts
    total_customers = Customer.query.count()
    active_laundries = Laundry.query.filter(Laundry.status != 'Completed').count()
    completed_laundries = Laundry.query.filter_by(status='Completed').count()
    
    # Calculate real revenue from completed laundries
    total_revenue = db.session.query(func.sum(Laundry.price)).filter(
        Laundry.status == 'Completed'
    ).scalar() or 0
    
    # Get popular services data
    popular_services = db.session.query(
        Service.name,
        func.count(Laundry.id).label('count')
    ).join(Service.laundries).group_by(Service.id).order_by(desc('count')).limit(5).all()
    
    # Service type counts
    wash_only_services = Service.query.filter(Service.category == 'Standard').count()
    dry_only_services = Service.query.filter(Service.category == 'Express').count()
    wash_dry_services = Service.query.filter(Service.category == 'Premium').count()
    total_services = Service.query.filter_by(is_active=True).count()
    
    # Prepare chart data
    chart_data = {
        'revenue': {
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'data': [
                round(total_revenue * 0.6, 2), 
                round(total_revenue * 0.7, 2), 
                round(total_revenue * 0.8, 2), 
                round(total_revenue * 0.9, 2), 
                round(total_revenue * 0.95, 2), 
                round(total_revenue, 2)
            ]
        },
        'services': {
            'labels': ['Standard', 'Express', 'Premium', 'Other'],
            'data': [
                wash_only_services, 
                dry_only_services, 
                wash_dry_services, 
                max(0, total_services - (wash_only_services + dry_only_services + wash_dry_services))
            ]
        },
        'status': {
            'labels': ['Pending', 'In Progress', 'Completed'],
            'data': [
                Laundry.query.filter_by(status='Pending').count(),
                active_laundries - Laundry.query.filter_by(status='Pending').count(),
                completed_laundries
            ]
        }
    }
    
    return render_template('charts.html', 
                         chart_data=json.dumps(chart_data),
                         total_customers=total_customers,
                         active_laundries=active_laundries,
                         completed_laundries=completed_laundries,
                         total_revenue=total_revenue,
                         popular_services=popular_services)


@views.route('/send_sms', methods=['POST'])
@login_required
@admin_required
def send_sms_route():
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({'success': False, 'message': 'Phone number and message are required'})
        
        # Use the SMS service to send the message
        result = sms_service.send_sms(phone_number, message)
        
        if result:
            return jsonify({'success': True, 'message': 'SMS sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send SMS'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending SMS: {str(e)}'})


@views.route('/toggle_widget', methods=['POST'])
@login_required
def toggle_widget():
    """Toggle widget visibility for current user"""
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


@views.route('/save_layout', methods=['POST'])
@login_required  
def save_layout():
    """Save the user's dashboard widget layout"""
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


@views.route('/save_widget_preferences', methods=['POST'])
@login_required
def save_widget_preferences():
    """Save user's dashboard widget preferences"""
    try:
        widget_config = request.json.get('widgets', [])
        
        # Clear existing widgets for the user
        DashboardWidget.query.filter_by(user_id=current_user.id).delete()
        
        # Add new widget preferences
        for widget_name in widget_config:
            if widget_name in get_default_widgets(current_user.role):
                widget = DashboardWidget(
                    user_id=current_user.id,
                    widget_id=widget_name,
                    is_visible=True,
                    position=widget_config.index(widget_name)
                )
                db.session.add(widget)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Widget preferences saved successfully!'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error saving preferences: {str(e)}'
        }), 500
