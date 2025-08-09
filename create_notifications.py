#!/usr/bin/env python3

"""
Helper script to create notifications for testing and system events
"""

from app import create_app, db
from app.models import User, Notification
from app.notifications import create_notification, create_system_notification

app = create_app()

def create_test_notifications():
    """Create various test notifications"""
    with app.app_context():
        admin_user = User.query.first()
        if not admin_user:
            print("No admin user found!")
            return
            
        print("Creating test notifications...")
        
        # System notifications
        create_system_notification(
            user_id=admin_user.id,
            title="System Update Available",
            message="A new system update is available with improved performance and bug fixes.",
            notification_type="info"
        )
        
        create_system_notification(
            user_id=admin_user.id,
            title="Backup Completed",
            message="Daily backup completed successfully. All data is secure.",
            notification_type="success"
        )
        
        create_system_notification(
            user_id=admin_user.id,
            title="Low Storage Warning",
            message="System storage is running low (85% full). Consider cleaning up old files.",
            notification_type="warning"
        )
        
        print("✅ Test notifications created successfully!")

def create_business_notifications():
    """Create business-related notifications"""
    with app.app_context():
        admin_user = User.query.first()
        if not admin_user:
            print("No admin user found!")
            return
            
        print("Creating business notifications...")
        
        create_notification(
            user_id=admin_user.id,
            title="Weekly Report Ready",
            message="Your weekly business report is ready for review. Check your revenue, expenses, and customer activity.",
            notification_type="info",
            action_url="/expenses/reports",
            action_text="View Report"
        )
        
        create_notification(
            user_id=admin_user.id,
            title="New Customer Milestone",
            message="Congratulations! You've reached 10 total customers in your laundry business.",
            notification_type="success"
        )
        
        create_notification(
            user_id=admin_user.id,
            title="Inventory Check Reminder",
            message="It's time for your monthly inventory check. Review stock levels and update quantities.",
            notification_type="warning",
            action_url="/inventory/dashboard",
            action_text="Check Inventory"
        )
        
        print("✅ Business notifications created successfully!")

if __name__ == "__main__":
    choice = input("Choose notification type to create:\n1. Test notifications\n2. Business notifications\n3. Both\nEnter choice (1-3): ")
    
    if choice in ['1', '3']:
        create_test_notifications()
    if choice in ['2', '3']:
        create_business_notifications()
    
    print("\n🎉 Notifications created! Visit /notifications to view them.")
