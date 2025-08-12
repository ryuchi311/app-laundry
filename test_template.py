#!/usr/bin/env python3
"""Test bulk message template rendering"""

from flask import Flask
from jinja2 import Template

def test_template():
    print("🧪 TESTING BULK SMS TEMPLATE...")
    
    try:
        app = Flask(__name__)
        with app.test_request_context():
            # Read template file
            with open('app/templates/bulk_message.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Create template
            template = Template(template_content)
            
            # Test render with sample data
            result = template.render(
                total_customers=4,
                customers_with_phones=4,
                recent_campaigns=[],
                sms_configured=True
            )
            
            print("✅ Template renders successfully!")
            print(f"📄 Template length: {len(result)} characters")
            print("✅ No Jinja2 syntax errors found!")
            print("🚀 Bulk message template is ready!")
            
    except Exception as e:
        print(f"❌ Template error: {str(e)}")
        return False
    
    return True

if __name__ == '__main__':
    test_template()
