#!/usr/bin/env python3
"""
Test script to verify dashboard template syntax is fixed.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, DashboardWidget

def test_template_syntax():
    """Test dashboard template syntax"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Dashboard Template Syntax Fix")
        print("=" * 45)
        
        try:
            # Test template compilation
            from jinja2 import Environment, FileSystemLoader
            
            # Create a test environment
            env = Environment(loader=FileSystemLoader('app/templates'))
            template = env.get_template('dashboard.html')
            print("✅ Dashboard template compiles successfully")
            
            # Test with Flask's template system
            with app.test_client() as client:
                with app.test_request_context('/'):
                    from flask import render_template_string, render_template
                    
                    # Try to load the template (this will catch any syntax errors)
                    try:
                        # We don't need to fully render it, just check it can be loaded
                        template = app.jinja_env.get_template('dashboard.html')
                        print("✅ Template loads successfully in Flask environment")
                    except Exception as e:
                        print(f"❌ Template loading failed: {str(e)}")
                        return False
            
            print("✅ No Jinja2 syntax errors found")
            print("\n" + "=" * 45)
            print("🎉 TEMPLATE SYNTAX FIX SUCCESSFUL!")
            print("\n📋 Summary:")
            print("   • Removed extra {% endblock %} tag")
            print("   • Template now compiles without errors")
            print("   • Dashboard route should work correctly")
            
            return True
            
        except Exception as e:
            print(f"❌ Template syntax test failed: {str(e)}")
            return False

def main():
    success = test_template_syntax()
    
    if success:
        print("\n🏁 Template syntax fix completed successfully!")
        print("Your dashboard should now load without errors.")
    else:
        print("\n💥 Template syntax fix failed!")
        print("Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
