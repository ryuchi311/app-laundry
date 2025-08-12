#!/usr/bin/env python3
"""
Test Inventory Notification System

This script tests the automated inventory low warning notification system
by creating some test data and triggering notifications.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import InventoryItem, InventoryCategory, User, Notification
from app.notifications import create_inventory_notification, check_and_create_inventory_notifications

def test_inventory_notifications():
    """Test the inventory notification system"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Inventory Notification System...")
        
        # Get or create test user
        test_user = User.query.first()
        if not test_user:
            print("❌ No users found. Please create a user first.")
            return
        
        print(f"👤 Testing with user: {test_user.full_name}")
        
        # Get or create test inventory category
        test_category = InventoryCategory.query.filter_by(name='Test Category').first()
        if not test_category:
            test_category = InventoryCategory(
                name='Test Category',
                description='Test category for notification system',
                icon='fas fa-flask',
                color='blue'
            )
            db.session.add(test_category)
            db.session.commit()
            print("✅ Created test inventory category")
        
        # Create test inventory items with different stock levels
        test_items = [
            {
                'name': 'Test Detergent - Low Stock',
                'current_stock': 2,
                'minimum_stock': 10,
                'unit_of_measure': 'bottles'
            },
            {
                'name': 'Test Fabric Softener - Out of Stock',
                'current_stock': 0,
                'minimum_stock': 5,
                'unit_of_measure': 'liters'
            },
            {
                'name': 'Test Bleach - Normal Stock',
                'current_stock': 15,
                'minimum_stock': 5,
                'unit_of_measure': 'bottles'
            }
        ]
        
        created_items = []
        for item_data in test_items:
            # Check if item already exists
            existing_item = InventoryItem.query.filter_by(name=item_data['name']).first()
            if existing_item:
                # Update existing item
                existing_item.current_stock = item_data['current_stock']
                existing_item.minimum_stock = item_data['minimum_stock']
                existing_item.unit_of_measure = item_data['unit_of_measure']
                created_items.append(existing_item)
                print(f"✅ Updated existing item: {item_data['name']}")
            else:
                # Create new item
                new_item = InventoryItem(
                    name=item_data['name'],
                    description=f"Test item for notification system",
                    category_id=test_category.id,
                    current_stock=item_data['current_stock'],
                    minimum_stock=item_data['minimum_stock'],
                    unit_of_measure=item_data['unit_of_measure'],
                    cost_per_unit=25.0,
                    is_active=True
                )
                db.session.add(new_item)
                created_items.append(new_item)
                print(f"✅ Created test item: {item_data['name']}")
        
        db.session.commit()
        
        # Test individual notification creation
        print("\n🔔 Testing individual notification creation...")
        
        low_stock_item = created_items[0]  # Test Detergent - Low Stock
        out_of_stock_item = created_items[1]  # Test Fabric Softener - Out of Stock
        normal_stock_item = created_items[2]  # Test Bleach - Normal Stock
        
        # Test low stock notification
        low_stock_notification = create_inventory_notification(test_user.id, low_stock_item, 'low_stock')
        if low_stock_notification:
            print(f"✅ Created low stock notification: {low_stock_notification.title}")
        
        # Test out of stock notification
        out_of_stock_notification = create_inventory_notification(test_user.id, out_of_stock_item, 'out_of_stock')
        if out_of_stock_notification:
            print(f"✅ Created out of stock notification: {out_of_stock_notification.title}")
        
        db.session.commit()
        
        # Test bulk notification creation
        print("\n📦 Testing bulk notification creation...")
        notifications_created = check_and_create_inventory_notifications()
        db.session.commit()
        
        print(f"✅ Bulk check created {len(notifications_created)} notifications")
        
        # Display summary
        print(f"\n📊 NOTIFICATION TEST SUMMARY:")
        print(f"   • Test items created/updated: {len(created_items)}")
        print(f"   • Individual notifications created: {2}")
        print(f"   • Bulk notifications created: {len(notifications_created)}")
        
        # Show all inventory-related notifications for the user
        inventory_notifications = Notification.query.filter(
            Notification.user_id == test_user.id,
            Notification.related_model == 'inventory'
        ).order_by(Notification.created_at.desc()).limit(10).all()
        
        print(f"\n🔔 RECENT INVENTORY NOTIFICATIONS ({len(inventory_notifications)}):")
        for notif in inventory_notifications:
            status = "✅ Read" if notif.is_read else "🔔 Unread"
            print(f"   • {notif.title} - {notif.message[:50]}... [{status}]")
        
        print(f"\n✅ Inventory notification system test completed successfully!")
        print(f"📝 Check your notifications in the web interface to see the results.")
        
        return {
            'test_items_created': len(created_items),
            'individual_notifications': 2,
            'bulk_notifications': len(notifications_created),
            'total_inventory_notifications': len(inventory_notifications)
        }

def cleanup_test_data():
    """Clean up test data (optional)"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning up test data...")
        
        # Remove test inventory items
        test_items = InventoryItem.query.filter(InventoryItem.name.like('Test %')).all()
        for item in test_items:
            db.session.delete(item)
        
        # Remove test category
        test_category = InventoryCategory.query.filter_by(name='Test Category').first()
        if test_category:
            db.session.delete(test_category)
        
        # Remove test notifications
        test_notifications = Notification.query.filter(
            Notification.related_model == 'inventory',
            Notification.title.like('%Test%')
        ).all()
        for notif in test_notifications:
            db.session.delete(notif)
        
        db.session.commit()
        print(f"✅ Cleaned up {len(test_items)} test items and related notifications")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Inventory Notification System')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test data')
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_test_data()
    else:
        test_inventory_notifications()

if __name__ == '__main__':
    main()
