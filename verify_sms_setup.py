#!/usr/bin/env python3
"""
Setup Verification Script for ACCIO Laundry Management System
This script verifies that all SMS dependencies and configurations are working.
"""

import sys
import os

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking Dependencies...")
    
    try:
        import requests
        print("   ✅ requests - OK")
    except ImportError:
        print("   ❌ requests - MISSING")
        return False
    
    try:
        from dotenv import load_dotenv
        print("   ✅ python-dotenv - OK")
    except ImportError:
        print("   ❌ python-dotenv - MISSING")
        return False
    
    try:
        import urllib.parse
        print("   ✅ urllib.parse - OK")
    except ImportError:
        print("   ❌ urllib.parse - MISSING")
        return False
    
    return True

def check_app_structure():
    """Check if all required files exist"""
    print("\n📁 Checking File Structure...")
    
    required_files = [
        'app/sms_service.py',
        'app/templates/sms_settings.html',
        'test_sms.py',
        'SMS_SETUP_GUIDE.md',
        '.env.example'
    ]
    
    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path} - EXISTS")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_good = False
    
    return all_good

def check_app_integration():
    """Check if SMS service can be imported"""
    print("\n🔧 Checking App Integration...")
    
    try:
        sys.path.append('.')
        from app.sms_service import sms_service, send_sms_notification
        print("   ✅ SMS service import - OK")
        
        # Check if SMS service can format phone numbers
        test_phone = sms_service.format_phone_number("09123456789")
        if test_phone == "639123456789":
            print("   ✅ Phone formatting - OK")
        else:
            print(f"   ⚠️  Phone formatting - UNEXPECTED ({test_phone})")
        
        return True
    except ImportError as e:
        print(f"   ❌ SMS service import - FAILED ({e})")
        return False
    except Exception as e:
        print(f"   ❌ SMS service test - FAILED ({e})")
        return False

def check_flask_routes():
    """Check if Flask routes are properly configured"""
    print("\n🌐 Checking Flask Routes...")
    
    try:
        from app import create_app
        app = create_app()
        
        # Check if SMS settings route exists
        sms_routes = [str(rule) for rule in app.url_map.iter_rules() if 'sms' in str(rule)]
        if sms_routes:
            print(f"   ✅ SMS routes - OK ({len(sms_routes)} found)")
            for route in sms_routes:
                print(f"      - {route}")
        else:
            print("   ❌ SMS routes - MISSING")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Flask routes check - FAILED ({e})")
        return False

def main():
    print("🧪 ACCIO Laundry SMS Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("File Structure", check_app_structure), 
        ("App Integration", check_app_integration),
        ("Flask Routes", check_flask_routes)
    ]
    
    all_passed = True
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"\n❌ Error during {check_name} check: {e}")
            results.append((check_name, False))
            all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name}: {status}")
    
    print(f"\nOverall Status: {'✅ ALL CHECKS PASSED' if all_passed else '❌ SOME CHECKS FAILED'}")
    
    if all_passed:
        print("\n🎉 SMS notifications are ready to use!")
        print("   Next steps:")
        print("   1. Configure your Semaphore API credentials")
        print("   2. Access /sms-settings in your browser")
        print("   3. Test with your phone number")
    else:
        print("\n🔧 Please fix the failed checks above before using SMS notifications.")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    exit(main())
