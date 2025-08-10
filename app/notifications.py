from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Notification

notifications = Blueprint('notifications', __name__)

@notifications.route('/notifications')
@login_required
def list_notifications():
    """Display all notifications for the current user"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', 'all')
    show_read = request.args.get('show_read', 'false').lower() == 'true'
    
    # Build query
    query = Notification.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if filter_type != 'all':
        query = query.filter_by(notification_type=filter_type)
    
    if not show_read:
        query = query.filter_by(is_read=False)
    
    # Order by most recent first
    notifications_data = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get counts for badges
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    total_count = Notification.query.filter_by(user_id=current_user.id).count()
    
    # Type counts
    type_counts = {
        'info': Notification.query.filter_by(user_id=current_user.id, notification_type='info', is_read=False).count(),
        'success': Notification.query.filter_by(user_id=current_user.id, notification_type='success', is_read=False).count(),
        'warning': Notification.query.filter_by(user_id=current_user.id, notification_type='warning', is_read=False).count(),
        'error': Notification.query.filter_by(user_id=current_user.id, notification_type='error', is_read=False).count(),
    }
    
    return render_template('notifications/list.html',
                         notifications=notifications_data,
                         unread_count=unread_count,
                         total_count=total_count,
                         type_counts=type_counts,
                         current_filter=filter_type,
                         show_read=show_read)

@notifications.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    
    return jsonify({
        'success': True,
        'message': 'Notification marked as read'
    })

@notifications.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read for the current user"""
    notifications_to_update = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    
    for notification in notifications_to_update:
        notification.mark_as_read()
    
    return jsonify({
        'success': True,
        'message': f'Marked {len(notifications_to_update)} notifications as read'
    })

@notifications.route('/notifications/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Notification deleted'
    })

@notifications.route('/notifications/api/unread-count')
@login_required
def get_unread_count():
    """API endpoint to get unread notification count"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    
    return jsonify({'count': count})

@notifications.route('/notifications/api/recent')
@login_required
def get_recent_notifications():
    """API endpoint to get recent notifications for dropdown"""
    recent = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    notifications_data = []
    for notification in recent:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message[:100] + ('...' if len(notification.message) > 100 else ''),
            'type': notification.notification_type,
            'is_read': notification.is_read,
            'time_ago': notification.get_time_ago(),
            'action_url': notification.action_url,
            'action_text': notification.action_text
        })
    
    return jsonify(notifications_data)


# Helper functions to create notifications
def create_notification(user_id, title, message, notification_type='info', 
                       related_model=None, related_id=None, 
                       action_url=None, action_text=None):
    """Helper function to create a new notification"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        related_model=related_model,
        related_id=related_id,
        action_url=action_url,
        action_text=action_text
    )
    
    db.session.add(notification)
    db.session.commit()
    return notification

def create_laundry_notification(user_id, laundry, message_type='status_update'):
    """Create laundry-related notifications"""
    messages = {
        'new_order': {
            'title': f'New Laundry #{laundry.laundry_id}',
            'message': f'New laundry received from {laundry.customer.full_name}. Service: {laundry.get_service_name()}',
            'type': 'info'
        },
        'status_update': {
            'title': f'Laundry #{laundry.laundry_id} Status Updated',
            'message': f'Laundry for {laundry.customer.full_name} is now {laundry.status}',
            'type': 'success'
        },
        'ready_pickup': {
            'title': f'Laundry #{laundry.laundry_id} Ready for Pickup',
            'message': f'Laundry for {laundry.customer.full_name} is ready for pickup',
            'type': 'warning'
        },
        'completed': {
            'title': f'Laundry #{laundry.laundry_id} Completed',
            'message': f'Laundry order for {laundry.customer.full_name} has been completed and delivered',
            'type': 'success'
        }
    }
    
    if message_type in messages:
        msg_data = messages[message_type]
        
        # Try to generate URL, fall back if not in request context
        action_url = None
        try:
            action_url = url_for('laundry.edit_laundry', laundry_id=laundry.laundry_id)
        except RuntimeError:
            # If we're not in a request context, create a basic URL
            action_url = f'/laundry/edit/{laundry.laundry_id}'
        
        return create_notification(
            user_id=user_id,
            title=msg_data['title'],
            message=msg_data['message'],
            notification_type=msg_data['type'],
            related_model='laundry',
            related_id=str(laundry.laundry_id),
            action_url=action_url,
            action_text='View Order'
        )

def create_customer_notification(user_id, customer, message_type='new_customer'):
    """Create customer-related notifications"""
    messages = {
        'new_customer': {
            'title': 'New Customer Registered',
            'message': f'New customer {customer.full_name} has been added to the system',
            'type': 'info'
        },
        'loyalty_tier_up': {
            'title': 'Customer Loyalty Tier Update',
            'message': f'{customer.full_name} has been promoted to a higher loyalty tier',
            'type': 'success'
        }
    }
    
    if message_type in messages:
        msg_data = messages[message_type]
        
        # Try to generate URL, fall back if not in request context
        action_url = None
        try:
            action_url = url_for('customer.view_customer', customer_id=customer.id)
        except RuntimeError:
            # If we're not in a request context, create a basic URL
            action_url = f'/customer/view/{customer.id}'
        
        return create_notification(
            user_id=user_id,
            title=msg_data['title'],
            message=msg_data['message'],
            notification_type=msg_data['type'],
            related_model='customer',
            related_id=str(customer.id),
            action_url=action_url,
            action_text='View Customer'
        )

def create_system_notification(user_id, title, message, notification_type='info'):
    """Create general system notifications"""
    return create_notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type
    )

def create_inventory_notification(user_id, inventory_item, message_type='low_stock'):
    """Create inventory-related notifications"""
    messages = {
        'low_stock': {
            'title': 'Inventory Low Warning',
            'message': f'Your {inventory_item.name} inventory is running low. Current stock: {inventory_item.current_stock} {inventory_item.unit_of_measure}. Consider restocking soon.',
            'type': 'warning'
        },
        'out_of_stock': {
            'title': 'Out of Stock Alert',
            'message': f'{inventory_item.name} is completely out of stock. Immediate restocking required.',
            'type': 'error'
        },
        'restock_reminder': {
            'title': 'Restock Reminder',
            'message': f'{inventory_item.name} stock is below minimum level ({inventory_item.minimum_stock} {inventory_item.unit_of_measure}). Current: {inventory_item.current_stock} {inventory_item.unit_of_measure}.',
            'type': 'warning'
        }
    }
    
    if message_type in messages:
        msg_data = messages[message_type]
        
        # Try to generate URL, fall back if not in request context
        action_url = None
        try:
            action_url = url_for('inventory.list_items')
        except RuntimeError:
            # If we're not in a request context, create a basic URL
            action_url = '/inventory/items'
        
        return create_notification(
            user_id=user_id,
            title=msg_data['title'],
            message=msg_data['message'],
            notification_type=msg_data['type'],
            related_model='inventory',
            related_id=str(inventory_item.id),
            action_url=action_url,
            action_text='Check Inventory'
        )

def check_and_create_inventory_notifications():
    """Check all inventory items and create notifications for low stock items"""
    from app.models import InventoryItem, User
    
    # Get all admin users (they should receive inventory notifications)
    admin_users = User.query.all()  # You might want to filter for admin users only
    
    # Get all low stock items
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.current_stock <= InventoryItem.minimum_stock,  # type: ignore
        InventoryItem.is_active == True  # type: ignore
    ).all()
    
    notifications_created = []
    
    for item in low_stock_items:
        for admin in admin_users:
            # Check if we already have a recent notification for this item
            from datetime import datetime, timedelta
            recent_notification = Notification.query.filter(
                Notification.user_id == admin.id,
                Notification.related_model == 'inventory',
                Notification.related_id == str(item.id),
                Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).first()
            
            # Only create notification if no recent one exists
            if not recent_notification:
                if item.current_stock <= 0:
                    notification = create_inventory_notification(admin.id, item, 'out_of_stock')
                else:
                    notification = create_inventory_notification(admin.id, item, 'low_stock')
                
                if notification:
                    notifications_created.append(notification)
    
    return notifications_created

@notifications.route('/api/check-inventory', methods=['POST'])
@login_required
def check_inventory_api():
    """API endpoint to manually trigger inventory level check"""
    try:
        notifications_created = check_and_create_inventory_notifications()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Inventory check completed. {len(notifications_created)} notifications created.',
            'notifications_count': len(notifications_created)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error checking inventory: {str(e)}'
        }), 500
