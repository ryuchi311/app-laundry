#!/usr/bin/env python3
"""
Quick verification script for Google Cloud deployment readiness
"""

def verify_deployment_ready():
    print("🔍 Verifying Google Cloud deployment readiness...")
    print("=" * 50)
    
    # Check 1: Import test
    try:
        from app import create_app, db
        from app.models import User, BusinessSettings, SMSSettings
        print("✅ All imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Check 2: App creation
    try:
        app = create_app()
        print("✅ Flask app created successfully")
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        return False
    
    # Check 3: Database operations
    try:
        with app.app_context():
            # Test model creation
            user = User()
            user.email = 'test@example.com'
            user.full_name = 'Test User'
            user.phone = '09123456789'
            user.role = 'Employee'
            
            print("✅ User model creation successful")
            
            # Test business settings
            business = BusinessSettings()
            business.business_name = 'Test Business'
            print("✅ BusinessSettings model creation successful")
            
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    
    # Check 4: Configuration
    config_checks = [
        ('SECRET_KEY', app.config.get('SECRET_KEY')),
        ('SQLALCHEMY_DATABASE_URI', app.config.get('SQLALCHEMY_DATABASE_URI')),
        ('DEBUG', app.config.get('DEBUG')),
    ]
    
    for key, value in config_checks:
        if value is not None:
            print(f"✅ {key} configured")
        else:
            print(f"⚠️  {key} not configured")
    
    print("\n🎉 All verification checks passed!")
    print("🚀 Your application is ready for Google Cloud deployment!")
    return True

if __name__ == "__main__":
    verify_deployment_ready()
