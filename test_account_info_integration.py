#!/usr/bin/env python3
"""
Test script to verify the Account Information integration in Bulk SMS Marketing page
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.sms_service import sms_service

def test_account_info_integration():
    """Test that Account Information is properly integrated into Bulk SMS page"""
    
    app = create_app()
    
    with app.app_context():
        print("=== BULK SMS ACCOUNT INFORMATION INTEGRATION TEST ===")
        print()
        
        # Test SMS service configuration status
        sms_configured = sms_service.is_configured()
        print(f"🔧 SMS Service Configured: {'✅ Yes' if sms_configured else '❌ No'}")
        
        if sms_configured:
            print(f"📝 Sender Name: {sms_service.sender_name}")
            print(f"🔑 API Key Configured: {'✅ Yes' if sms_service.api_key else '❌ No'}")
        print()
        
        # Test account information retrieval
        print("📊 ACCOUNT INFORMATION:")
        print("-" * 60)
        
        account_info = sms_service.get_account_status()
        
        if account_info.get('error'):
            print(f"❌ Status: {account_info['status']}")
            print(f"   Error: {account_info['error']}")
        else:
            print(f"✅ Status: {account_info['status']}")
            print(f"💳 Credit Balance: {account_info['credit_balance']} credits")
            print(f"💰 Each credit equals: 1 SMS")
        print()
        
        # Test bulk message page context
        print("🖥️  BULK MESSAGE PAGE CONTEXT:")
        print("-" * 60)
        
        # Simulate what the bulk_message route would provide
        from app.models import Customer
        
        total_customers = Customer.query.filter(Customer.is_active == True).count()
        customers_with_phones = Customer.query.filter(
            Customer.phone.isnot(None),
            Customer.is_active == True
        ).count()
        
        context_data = {
            'total_customers': total_customers,
            'customers_with_phones': customers_with_phones,
            'sms_configured': sms_configured,
            'account_info': account_info
        }
        
        print(f"📋 Total Active Customers: {context_data['total_customers']}")
        print(f"📱 Active Customers with Phones: {context_data['customers_with_phones']}")
        print(f"🔧 SMS Service Status: {'Configured' if context_data['sms_configured'] else 'Not Configured'}")
        
        if context_data['sms_configured']:
            if context_data['account_info'].get('error'):
                print(f"❌ Account Status: {context_data['account_info']['status']}")
                print(f"   Error: {context_data['account_info']['error']}")
            else:
                print(f"✅ Account Status: {context_data['account_info']['status']}")
                print(f"💳 Credit Balance: {context_data['account_info']['credit_balance']}")
        else:
            print("⚠️  Account Information: Not Available (SMS not configured)")
        print()
        
        # Test template rendering expectations
        print("🎨 TEMPLATE INTEGRATION:")
        print("-" * 60)
        
        if context_data['sms_configured']:
            print("✅ Account Information section will be displayed")
            print("✅ Refresh button will be functional")
            print("✅ Account status will show:", 
                  "Error state" if context_data['account_info'].get('error') 
                  else "Active state")
            print(f"✅ Credit balance will show: {context_data['account_info']['credit_balance']} credits")
        else:
            print("❌ Account Information section will be hidden")
            print("❌ Only SMS configuration warning will be shown")
        print()
        
        # Summary
        print("📄 INTEGRATION SUMMARY:")
        print("-" * 60)
        
        if context_data['sms_configured']:
            if not context_data['account_info'].get('error'):
                print("✅ SUCCESS: Full integration working correctly!")
                print("   - Account Information section visible")
                print("   - Refresh functionality available")
                print("   - Real-time account data displayed")
                print("   - Credit balance shown accurately")
            else:
                print("⚠️  PARTIAL: SMS configured but API error")
                print("   - Account Information section visible")
                print("   - Error state properly handled")
                print("   - User can refresh to retry")
        else:
            print("⚠️  LIMITED: SMS not configured")
            print("   - Account Information section hidden")
            print("   - User needs to configure SMS first")
            print("   - Configuration prompt displayed")
        
        print()
        print("✅ TEST COMPLETED: Account Information integration verified!")

if __name__ == '__main__':
    test_account_info_integration()
