#!/usr/bin/env python3
"""
Migration script to create the dashboard_widget table for customizable dashboards.
Run this script to add the DashboardWidget table to your database.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import DashboardWidget

def create_dashboard_widget_table():
    """Create the dashboard_widget table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ Successfully created dashboard_widget table")
            
            # Check if table was created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'dashboard_widget' in tables:
                print("✅ Dashboard widget table confirmed in database")
                
                # Get table info
                columns = inspector.get_columns('dashboard_widget')
                print(f"📋 Table has {len(columns)} columns:")
                for col in columns:
                    print(f"   - {col['name']} ({col['type']})")
            else:
                print("❌ Dashboard widget table not found in database")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating dashboard widget table: {str(e)}")
            return False

def test_dashboard_widget_operations():
    """Test basic operations on the DashboardWidget table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Test creating a widget
            test_widget = DashboardWidget(
                user_id=1,
                widget_id='stats_overview',
                position=0,
                widget_size='large'
            )
            
            db.session.add(test_widget)
            db.session.commit()
            print("✅ Successfully created test dashboard widget")
            
            # Test querying the widget
            widget = DashboardWidget.query.filter_by(user_id=1).first()
            if widget:
                print(f"✅ Successfully queried widget: {widget.widget_id}")
                print(f"   Position: {widget.position}, Size: {widget.widget_size}, Visible: {widget.is_visible}")
            
            # Clean up test data
            DashboardWidget.query.filter_by(user_id=1).delete()
            db.session.commit()
            print("✅ Test data cleaned up")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error testing dashboard widget operations: {str(e)}")
            return False

def main():
    print("🚀 Starting Dashboard Widget Migration...")
    print("=" * 50)
    
    # Create the table
    if create_dashboard_widget_table():
        print("\n🧪 Testing dashboard widget operations...")
        if test_dashboard_widget_operations():
            print("\n✅ Dashboard widget migration completed successfully!")
            print("\nNext steps:")
            print("1. Restart your Flask application")
            print("2. Visit /dashboard/customize to set up your widgets")
            print("3. Customize your dashboard layout")
        else:
            print("\n❌ Dashboard widget migration completed but tests failed")
    else:
        print("\n❌ Dashboard widget migration failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
