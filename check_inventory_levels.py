#!/usr/bin/env python3
"""
Inventory Level Checker Script

This script checks all inventory items for low stock levels and creates 
notifications for administrators. It can be run manually or scheduled
as a cron job/task scheduler.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import InventoryItem, User, Notification
from app.notifications import create_inventory_notification
from datetime import datetime, timedelta

def check_inventory_levels():
    """Check all inventory items and create notifications for low stock"""
    app = create_app()
    
    with app.app_context():
        print("🔍 Checking inventory levels...")
        
        # Get all active inventory items
        items = InventoryItem.query.filter_by(is_active=True).all()
        
        # Get all admin users (you might want to filter for specific roles)
        users = User.query.all()
        
        low_stock_items = []
        out_of_stock_items = []
        notifications_created = 0
        
        for item in items:
            # Check stock levels
            if item.current_stock <= 0:
                out_of_stock_items.append(item)
                print(f"❌ OUT OF STOCK: {item.name} (0 {item.unit_of_measure})")
                
                # Create notifications for all users
                for user in users:
                    if not has_recent_notification(user.id, item.id, 'error'):
                        create_inventory_notification(user.id, item, 'out_of_stock')
                        notifications_created += 1
                        
            elif item.current_stock <= item.minimum_stock:
                low_stock_items.append(item)
                print(f"⚠️  LOW STOCK: {item.name} ({item.current_stock}/{item.minimum_stock} {item.unit_of_measure})")
                
                # Create notifications for all users
                for user in users:
                    if not has_recent_notification(user.id, item.id, 'warning'):
                        create_inventory_notification(user.id, item, 'low_stock')
                        notifications_created += 1
        
        # Commit all notifications
        db.session.commit()
        
        # Print summary
        print(f"\n📊 INVENTORY SUMMARY:")
        print(f"   • Total items checked: {len(items)}")
        print(f"   • Out of stock: {len(out_of_stock_items)}")
        print(f"   • Low stock: {len(low_stock_items)}")
        print(f"   • Notifications created: {notifications_created}")
        
        if len(out_of_stock_items) + len(low_stock_items) == 0:
            print("✅ All inventory items are well stocked!")
        
        return {
            'total_items': len(items),
            'out_of_stock': len(out_of_stock_items),
            'low_stock': len(low_stock_items),
            'notifications_created': notifications_created,
            'out_of_stock_items': [{'name': item.name, 'stock': item.current_stock} for item in out_of_stock_items],
            'low_stock_items': [{'name': item.name, 'stock': item.current_stock, 'min': item.minimum_stock} for item in low_stock_items]
        }

def has_recent_notification(user_id, item_id, notification_type):
    """Check if user already has a recent notification for this item"""
    recent_notification = Notification.query.filter(
        Notification.user_id == user_id,
        Notification.related_model == 'inventory',
        Notification.related_id == str(item_id),
        Notification.notification_type == notification_type,
        Notification.created_at >= datetime.utcnow() - timedelta(hours=24)
    ).first()
    
    return recent_notification is not None

def main():
    """Main function to run the inventory check"""
    try:
        result = check_inventory_levels()
        
        # Exit with appropriate code
        if result['out_of_stock'] > 0:
            print("\n🚨 CRITICAL: Items are out of stock!")
            sys.exit(2)  # Critical warning
        elif result['low_stock'] > 0:
            print("\n⚠️  WARNING: Items are low on stock!")
            sys.exit(1)  # Warning
        else:
            print("\n✅ All inventory levels are healthy!")
            sys.exit(0)  # Success
            
    except Exception as e:
        print(f"❌ ERROR: Failed to check inventory levels: {e}")
        sys.exit(3)  # Error

if __name__ == '__main__':
    main()
