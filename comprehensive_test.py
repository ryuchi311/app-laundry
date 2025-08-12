#!/usr/bin/env python3
"""
Comprehensive test of the Bulk SMS Marketing System
"""

from app import create_app
from app.models import Customer, BulkMessageHistory, SMSSettings
from app.sms_service import sms_service

def run_comprehensive_test():
    """Run comprehensive system test"""
    app = create_app()
    with app.app_context():
        print("🧪 COMPREHENSIVE BULK SMS SYSTEM TEST")
        print("=" * 50)
        
        # Test 1: Database Models
        print("\n1️⃣ Testing Database Models...")
        customers = Customer.query.all()
        print(f"   ✅ Customers loaded: {len(customers)}")
        
        sms_settings = SMSSettings.query.first()
        print(f"   ✅ SMS Settings: {'Configured' if sms_settings else 'Not configured'}")
        
        campaigns = BulkMessageHistory.query.all()
        print(f"   ✅ Campaign history: {len(campaigns)} records")
        
        # Test 2: SMS Service
        print("\n2️⃣ Testing SMS Service...")
        print(f"   ✅ SMS Service configured: {sms_service.is_configured()}")
        print(f"   ✅ API Key: {'Set' if sms_service.api_key else 'Not set'}")
        print(f"   ✅ Sender Name: {sms_service.sender_name or 'Not set'}")
        
        # Test 3: Customer Data Quality
        print("\n3️⃣ Testing Customer Data...")
        customers_with_phones = [c for c in customers if c.phone and c.phone.strip()]
        print(f"   ✅ Total customers: {len(customers)}")
        print(f"   ✅ Customers with phones: {len(customers_with_phones)}")
        
        if customers_with_phones:
            print("   📱 Customer phone numbers:")
            for c in customers_with_phones[:3]:  # Show first 3
                print(f"      - {c.full_name}: {c.phone}")
        
        # Test 4: Bulk Message History Model
        print("\n4️⃣ Testing BulkMessageHistory Model...")
        test_history = BulkMessageHistory()
        test_history.message_text = "Test promotional message with {customer_name}"
        test_history.message_type = "promo"
        test_history.sent_by_user_id = 1
        test_history.total_recipients = 10
        test_history.successful_sends = 8
        test_history.failed_sends = 2
        
        print(f"   ✅ Success rate calculation: {test_history.get_success_rate()}%")
        print(f"   ✅ Time since sent: {test_history.get_time_since_sent()}")
        
        # Test 5: Message Templates
        print("\n5️⃣ Testing Message Templates...")
        sample_templates = [
            "🎉 Special offer for you, {customer_name}! Get 20% off your next laundry service this week only. Visit {sender_name} today!",
            "Hi {customer_name}! 🧺 New service alert: We now offer same-day dry cleaning! Drop off by 10AM, pick up by 5PM. - {sender_name}",
            "🎊 {customer_name}, it's our anniversary month! Enjoy buy 2 get 1 FREE on all wash & fold services throughout August. - {sender_name}"
        ]
        
        for i, template in enumerate(sample_templates, 1):
            formatted = template.replace('{customer_name}', 'John Doe').replace('{sender_name}', 'ACCIOWash')
            print(f"   ✅ Template {i}: {len(formatted)} chars - {formatted[:50]}...")
        
        # Test 6: System Readiness
        print("\n6️⃣ System Readiness Check...")
        issues = []
        
        if not sms_service.is_configured():
            issues.append("SMS service not configured")
        
        if len(customers_with_phones) == 0:
            issues.append("No customers with phone numbers")
        
        if not sms_settings:
            issues.append("SMS settings not initialized")
        
        if issues:
            print("   ⚠️ Issues found:")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ All systems ready!")
        
        # Summary
        print("\n" + "=" * 50)
        print("🎯 BULK SMS MARKETING SYSTEM STATUS")
        print("=" * 50)
        print(f"📊 System Status: {'READY' if not issues else 'NEEDS ATTENTION'}")
        print(f"👥 Total Customers: {len(customers)}")
        print(f"📱 SMS Ready Customers: {len(customers_with_phones)}")
        print(f"📈 Previous Campaigns: {len(campaigns)}")
        print(f"🔧 SMS Service: {'CONFIGURED' if sms_service.is_configured() else 'NOT CONFIGURED'}")
        print(f"🌐 Access URL: http://127.0.0.1:5000/sms-settings/bulk-message")
        
        if not issues:
            print("\n🚀 READY TO SEND BULK SMS CAMPAIGNS!")
        else:
            print(f"\n⚠️ Please address {len(issues)} issue(s) before using bulk SMS")
        
        print("=" * 50)

if __name__ == '__main__':
    run_comprehensive_test()
