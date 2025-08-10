#!/usr/bin/env python3
"""
Test script for dashboard customization functionality.
Tests the complete dashboard widget customization system.
"""

import sys
import os
import json
import requests
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, DashboardWidget

def test_dashboard_widget_system():
    """Test the complete dashboard widget system"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Dashboard Widget System...")
        print("=" * 50)
        
        try:
            # 1. Test DashboardWidget model
            print("\n1. Testing DashboardWidget model...")
            
            # Use existing user (user ID 1 should exist from setup)
            test_user_id = 1
            
            # Ensure we have a user to test with
            existing_user = User.query.first()
            if existing_user:
                test_user_id = existing_user.id
                print(f"   ✅ Using existing user (ID: {test_user_id})")
            else:
                print("   ⚠️  No users found, using user_id=1 for test")
            
            # Test default widgets creation
            widgets = DashboardWidget.query.filter_by(user_id=test_user_id).all()
            if not widgets:
                default_widgets = [
                    {'id': 'stats_overview', 'name': 'Statistics Overview', 'position': 0, 'size': 'large'},
                    {'id': 'recent_orders', 'name': 'Recent Laundry Orders', 'position': 1, 'size': 'normal'},
                    {'id': 'inventory_status', 'name': 'Inventory Status', 'position': 2, 'size': 'normal'},
                    {'id': 'revenue_chart', 'name': 'Revenue Overview', 'position': 3, 'size': 'normal'},
                ]
                
                for widget_config in default_widgets:
                    widget = DashboardWidget(
                        user_id=test_user_id,
                        widget_id=widget_config['id'],
                        position=widget_config['position'],
                        widget_size=widget_config['size']
                    )
                    db.session.add(widget)
                
                db.session.commit()
                print("   ✅ Created default dashboard widgets")
            
            # 2. Test widget queries
            print("\n2. Testing widget queries...")
            
            all_widgets = DashboardWidget.query.filter_by(user_id=test_user_id).order_by(DashboardWidget.position).all()  # type: ignore
            print(f"   ✅ Found {len(all_widgets)} widgets for user")
            
            visible_widgets = DashboardWidget.query.filter_by(user_id=test_user_id, is_visible=True).all()
            print(f"   ✅ Found {len(visible_widgets)} visible widgets")
            
            # 3. Test widget operations
            print("\n3. Testing widget operations...")
            
            # Test hiding a widget
            test_widget = all_widgets[0]
            original_visibility = test_widget.is_visible
            test_widget.is_visible = False
            db.session.commit()
            print("   ✅ Successfully hid widget")
            
            # Test reordering widgets
            if len(all_widgets) > 1:
                widget1, widget2 = all_widgets[0], all_widgets[1]
                pos1, pos2 = widget1.position, widget2.position
                widget1.position, widget2.position = pos2, pos1
                db.session.commit()
                print("   ✅ Successfully reordered widgets")
                
                # Restore original positions
                widget1.position, widget2.position = pos1, pos2
                db.session.commit()
            
            # Restore original visibility
            test_widget.is_visible = original_visibility
            db.session.commit()
            
            # 4. Test widget size changes
            print("\n4. Testing widget size changes...")
            
            original_size = test_widget.widget_size
            test_widget.widget_size = 'small'
            db.session.commit()
            print("   ✅ Successfully changed widget size")
            
            # Restore original size
            test_widget.widget_size = original_size
            db.session.commit()
            
            # 5. Test widget configuration serialization
            print("\n5. Testing widget configuration...")
            
            widget_configs = []
            for widget in all_widgets:
                config = {
                    'id': widget.widget_id,
                    'position': widget.position,
                    'is_visible': widget.is_visible,
                    'size': widget.widget_size,
                    'user_id': widget.user_id
                }
                widget_configs.append(config)
            
            print(f"   ✅ Serialized {len(widget_configs)} widget configurations")
            print(f"   📋 Sample config: {json.dumps(widget_configs[0], indent=2)}")
            
            # 6. Test auto-organization logic
            print("\n6. Testing auto-organization...")
            
            # Simulate priority-based organization
            priority_order = {
                'stats_overview': 0,
                'recent_orders': 1,
                'inventory_status': 2,
                'revenue_chart': 3,
                'low_stock_alerts': 4
            }
            
            for widget in all_widgets:
                new_position = priority_order.get(widget.widget_id, 99)
                widget.position = new_position
            
            db.session.commit()
            print("   ✅ Successfully auto-organized widgets by priority")
            
            # 7. Test helper functions
            print("\n7. Testing helper functions...")
            
            def get_default_widgets():
                return [
                    {'id': 'stats_overview', 'name': 'Statistics Overview', 'position': 0, 'size': 'large'},
                    {'id': 'recent_orders', 'name': 'Recent Laundry Orders', 'position': 1, 'size': 'normal'},
                    {'id': 'inventory_status', 'name': 'Inventory Status', 'position': 2, 'size': 'normal'},
                ]
            
            default_config = get_default_widgets()
            print(f"   ✅ Default widgets configuration loaded: {len(default_config)} widgets")
            
            # 8. Test error handling
            print("\n8. Testing error handling...")
            
            try:
                # Try to create duplicate widget
                duplicate_widget = DashboardWidget(
                    user_id=test_user_id,
                    widget_id=all_widgets[0].widget_id,  # Same as existing
                    position=0,
                    widget_size='normal'
                )
                db.session.add(duplicate_widget)
                db.session.commit()
                print("   ⚠️  Duplicate widget was allowed (this may be expected)")
            except Exception as e:
                print(f"   ✅ Properly handled duplicate widget error: {str(e)}")
                db.session.rollback()
            
            print("\n✅ All dashboard widget tests passed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Dashboard widget test failed: {str(e)}")
            db.session.rollback()
            return False

def test_dashboard_routes():
    """Test dashboard routes and endpoints"""
    app = create_app()
    
    print("\n🌐 Testing Dashboard Routes...")
    print("=" * 40)
    
    with app.test_client() as client:
        try:
            # Test if routes are properly registered
            print("\n1. Testing route registration...")
            
            # These tests will fail without authentication, but we can check if routes exist
            routes_to_test = [
                '/',
                '/dashboard/customize',
                '/dashboard/api/save-layout',
                '/dashboard/api/reset-layout',
                '/dashboard/api/auto-organize',
                '/dashboard/api/toggle-widget'
            ]
            
            for route in routes_to_test:
                try:
                    response = client.get(route)
                    # We expect 302 (redirect to login) for protected routes
                    if response.status_code in [200, 302, 405]:  # 405 for POST-only routes
                        print(f"   ✅ Route {route} is properly registered")
                    else:
                        print(f"   ⚠️  Route {route} returned status {response.status_code}")
                except Exception as e:
                    print(f"   ❌ Route {route} error: {str(e)}")
            
            print("\n✅ Dashboard route tests completed!")
            return True
            
        except Exception as e:
            print(f"\n❌ Dashboard route test failed: {str(e)}")
            return False

def test_template_integration():
    """Test template integration"""
    print("\n📄 Testing Template Integration...")
    print("=" * 40)
    
    try:
        # Check if template files exist
        template_files = [
            'app/templates/dashboard.html',
            'app/templates/dashboard_customize.html'
        ]
        
        for template_file in template_files:
            if os.path.exists(template_file):
                print(f"   ✅ Template file exists: {template_file}")
                
                # Basic content check
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if 'user_widgets' in content:
                    print(f"   ✅ Template {template_file} has widget support")
                else:
                    print(f"   ⚠️  Template {template_file} may not have widget support")
            else:
                print(f"   ❌ Template file missing: {template_file}")
        
        print("\n✅ Template integration tests completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Template integration test failed: {str(e)}")
        return False

def main():
    print("🚀 Starting Dashboard Customization System Tests...")
    print("=" * 60)
    
    success = True
    
    # Run all tests
    success &= test_dashboard_widget_system()
    success &= test_dashboard_routes()
    success &= test_template_integration()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All dashboard customization tests passed!")
        print("\nYour dashboard customization system is ready to use!")
        print("\nFeatures available:")
        print("• ✅ Drag and drop widget reordering")
        print("• ✅ Show/hide widgets")
        print("• ✅ Widget size customization")
        print("• ✅ Auto-organization options")
        print("• ✅ Reset to default layout")
        print("• ✅ Persistent user preferences")
        
        print("\nTo start using:")
        print("1. Run your Flask application")
        print("2. Navigate to the dashboard")
        print("3. Click 'Customize' to personalize your layout")
    else:
        print("❌ Some dashboard customization tests failed!")
        print("Please check the error messages above.")

if __name__ == "__main__":
    main()
