#!/usr/bin/env python3

from app import create_app, db
from app.models import User, Notification, Laundry, Customer

app = create_app()

def create_sample_notifications():
    with app.app_context():
        print("=== Creating Sample Notifications ===")
        
        # Get the admin user (assuming ID 1)
        admin_user = User.query.first()
        if not admin_user:
            print("No admin user found! Please create a user first.")
            return
        
        print(f"Creating notifications for user: {admin_user.email}")
        
        # Clear existing notifications for clean test
        Notification.query.filter_by(user_id=admin_user.id).delete()
        db.session.commit()
        
        # Create sample notifications
        notifications_to_create = [
            {
                'title': 'Welcome to ACCIO Laundry!',
                'message': 'Welcome to your laundry management system. You can now track orders, manage customers, and monitor your business performance.',
                'notification_type': 'success'
            },
            {
                'title': 'New Customer Alert',
                'message': 'A new customer "John Doe" has been added to your system. They are now eligible for loyalty program benefits.',
                'notification_type': 'info',
                'related_model': 'customer',
                'related_id': '1',
                'action_url': '/customer/list',
                'action_text': 'View Customers'
            },
            {
                'title': 'Inventory Low Warning',
                'message': 'Your detergent inventory is running low. Current stock: 2 units. Consider restocking soon.',
                'notification_type': 'warning',
                'action_url': '/inventory',
                'action_text': 'Check Inventory'
            },
            {
                'title': 'System Maintenance',
                'message': 'A system backup was completed successfully. All your data is secure and up to date.',
                'notification_type': 'success'
            },
            {
                'title': 'Payment Reminder',
                'message': 'Monthly subscription payment is due in 3 days. Please ensure your payment method is up to date.',
                'notification_type': 'warning'
            }
        ]
        
        # Add laundry-specific notifications if laundries exist
        recent_laundries = Laundry.query.order_by(Laundry.date_received.desc()).limit(2).all()
        for laundry in recent_laundries:
            notifications_to_create.append({
                'title': f'Laundry Order #{laundry.laundry_id} Status Update',
                'message': f'Laundry order for {laundry.customer.full_name} is currently {laundry.status}. Service: {laundry.get_service_name()}',
                'notification_type': 'info',
                'related_model': 'laundry',
                'related_id': laundry.laundry_id,
                'action_url': f'/laundry/edit/{laundry.laundry_id}',
                'action_text': 'View Order'
            })
        
        # Create the notifications
        for i, notif_data in enumerate(notifications_to_create):
            notification = Notification(
                user_id=admin_user.id,
                title=notif_data['title'],
                message=notif_data['message'],
                notification_type=notif_data['notification_type'],
                related_model=notif_data.get('related_model'),
                related_id=notif_data.get('related_id'),
                action_url=notif_data.get('action_url'),
                action_text=notif_data.get('action_text')
            )
            
            # Make some notifications already read
            if i >= 3:
                notification.is_read = False  # Keep recent ones unread
            else:
                notification.is_read = True if i % 2 == 0 else False  # Mix read/unread for older ones
            
            db.session.add(notification)
        
        db.session.commit()
        
        # Display created notifications
        all_notifications = Notification.query.filter_by(user_id=admin_user.id).order_by(Notification.created_at.desc()).all()
        print(f"\nCreated {len(all_notifications)} notifications:")
        
        for notification in all_notifications:
            status = "✓ Read" if notification.is_read else "● Unread"
            print(f"  {status} [{notification.notification_type.upper()}] {notification.title}")
            print(f"    {notification.message[:80]}{'...' if len(notification.message) > 80 else ''}")
            if notification.action_text:
                print(f"    Action: {notification.action_text}")
            print()
        
        unread_count = Notification.query.filter_by(user_id=admin_user.id, is_read=False).count()
        print(f"Total unread notifications: {unread_count}")

if __name__ == "__main__":
    create_sample_notifications()
