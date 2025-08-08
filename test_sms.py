#!/usr/bin/env python3
"""
SMS Test Script for ACCIO Laundry Management System
This script allows you to test SMS functionality independently.
"""

import sys
import os
sys.path.append('.')

from app.sms_service import send_sms_notification, sms_service

def test_sms():
    print("🧪 ACCIO Laundry SMS Test Script")
    print("=" * 50)
    
    # Check configuration
    print("\n📋 Configuration Status:")
    print(f"   API Key: {'✅ Set' if sms_service.api_key else '❌ Not set'}")
    print(f"   Sender Name: {'✅ Set' if sms_service.sender_name else '❌ Not set'} ({sms_service.sender_name})")
    print(f"   Service Configured: {'✅ Yes' if sms_service.is_configured() else '❌ No'}")
    
    if not sms_service.is_configured():
        print("\n❌ SMS service is not configured!")
        print("   Please set the following environment variables:")
        print("   - SEMAPHORE_API_KEY")
        print("   - SEMAPHORE_SENDER_NAME")
        print("\n   Or configure through the web interface at /sms-settings")
        return
    
    # Get test phone number
    print("\n📱 Enter test phone number:")
    phone = input("   Phone number (e.g., 09123456789): ").strip()
    
    if not phone:
        print("❌ No phone number provided!")
        return
    
    # Format phone number
    formatted_phone = sms_service.format_phone_number(phone)
    print(f"   Original: {phone}")
    print(f"   Formatted: {formatted_phone}")
    
    # Test messages
    test_messages = [
        {
            'name': 'Welcome Message',
            'message': f'Welcome to ACCIO Laundry! This is a test message from {sms_service.sender_name}. SMS notifications are working! 🎉'
        },
        {
            'name': 'Status Update',
            'message': f'Hi! Your laundry (#TEST001) is ready for pickup. Please visit us during business hours. - {sms_service.sender_name}'
        }
    ]
    
    print(f"\n🚀 Ready to send test messages to {formatted_phone}")
    print("   Available test messages:")
    for i, msg in enumerate(test_messages, 1):
        print(f"   {i}. {msg['name']}")
    print("   0. Send custom message")
    print("   q. Quit")
    
    while True:
        choice = input("\n   Choose option: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == '0':
            custom_msg = input("   Enter custom message: ").strip()
            if custom_msg:
                print(f"\n📤 Sending custom message...")
                if formatted_phone:
                    success = send_sms_notification(formatted_phone, custom_msg)
                    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
                else:
                    print("   ❌ Invalid phone number format!")
        elif choice in ['1', '2']:
            idx = int(choice) - 1
            msg_data = test_messages[idx]
            print(f"\n📤 Sending {msg_data['name']}...")
            print(f"   Message: {msg_data['message'][:50]}...")
            if formatted_phone:
                success = send_sms_notification(formatted_phone, msg_data['message'])
                print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
            else:
                print("   ❌ Invalid phone number format!")
        else:
            print("   Invalid option. Please try again.")

def show_help():
    print("📱 ACCIO Laundry SMS Test Script")
    print("=" * 50)
    print("\nUsage:")
    print("   python test_sms.py          - Interactive test mode")
    print("   python test_sms.py help     - Show this help")
    print("   python test_sms.py quick <phone> <message> - Quick send")
    print("\nExamples:")
    print("   python test_sms.py")
    print("   python test_sms.py quick 09123456789 'Test message'")
    print("\nEnvironment Variables:")
    print("   SEMAPHORE_API_KEY    - Your Semaphore API key")
    print("   SEMAPHORE_SENDER_NAME - Your sender name")

def quick_send(phone, message):
    print(f"📤 Quick SMS send to {phone}")
    print(f"   Message: {message}")
    
    if not sms_service.is_configured():
        print("❌ SMS service not configured!")
        return
    
    if not phone:
        print("❌ No phone number provided!")
        return
    
    formatted_phone = sms_service.format_phone_number(phone)
    if not formatted_phone:
        print("❌ Invalid phone number format!")
        return
    
    success = send_sms_notification(formatted_phone, message)
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'help':
            show_help()
        elif sys.argv[1].lower() == 'quick' and len(sys.argv) >= 4:
            phone = sys.argv[2]
            message = ' '.join(sys.argv[3:])
            quick_send(phone, message)
        else:
            print("❌ Invalid arguments. Use 'python test_sms.py help' for usage.")
    else:
        test_sms()
