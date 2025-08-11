#!/usr/bin/env python3
"""
Pre-deployment test script
Run this to verify your application works before deploying to Google Cloud
"""

import os
import sys
import subprocess
import requests
import time
from threading import Timer

def run_tests():
    print("🧪 Pre-Deployment Testing for Google Cloud")
    print("=" * 50)
    
    # Test 1: Check required files exist
    print("\n1️⃣ Checking deployment files...")
    required_files = [
        'main.py',
        'app.yaml', 
        'requirements.txt',
        '.gcloudignore',
        'app/__init__.py'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    
    # Test 2: Install dependencies
    print("\n2️⃣ Checking dependencies...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print(f"❌ Dependency installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False
    
    # Test 3: App can start
    print("\n3️⃣ Testing application startup...")
    try:
        # Import and create app
        from app import create_app
        app = create_app()
        
        if app:
            print("✅ Application created successfully")
            
            # Test app configuration
            print(f"✅ Debug mode: {app.debug}")
            print(f"✅ Secret key configured: {'SECRET_KEY' in app.config}")
            
        else:
            print("❌ Failed to create application")
            return False
            
    except Exception as e:
        print(f"❌ Application startup failed: {e}")
        return False
    
    # Test 4: Database creation
    print("\n4️⃣ Testing database setup...")
    try:
        from app import db
        with app.app_context():
            # Try to create tables
            db.create_all()
            
            # Test basic model import
            from app.models import User, BusinessSettings, SMSSettings
            print("✅ Database tables created")
            print("✅ Models imported successfully")
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    # Test 5: Basic route testing
    print("\n5️⃣ Testing routes...")
    try:
        with app.test_client() as client:
            # Test home route
            response = client.get('/')
            if response.status_code in [200, 302]:  # 302 for redirect to login
                print("✅ Home route accessible")
            else:
                print(f"❌ Home route failed: {response.status_code}")
                return False
            
            # Test login route
            response = client.get('/auth/login')
            if response.status_code == 200:
                print("✅ Login route accessible")
            else:
                print(f"❌ Login route failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        return False
    
    # Test 6: Production configuration
    print("\n6️⃣ Testing production configuration...")
    
    # Set production environment
    os.environ['GAE_ENV'] = 'standard'
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        prod_app = create_app()
        
        if not prod_app.debug:
            print("✅ Debug mode disabled in production")
        else:
            print("⚠️  Warning: Debug mode still enabled")
        
        print(f"✅ Database URI configured: {bool(prod_app.config.get('SQLALCHEMY_DATABASE_URI'))}")
        
    except Exception as e:
        print(f"❌ Production configuration failed: {e}")
        return False
    finally:
        # Clean up environment
        os.environ.pop('GAE_ENV', None)
        os.environ.pop('FLASK_ENV', None)
    
    print("\n🎉 All tests passed! Your application is ready for Google Cloud deployment.")
    print("\n📋 Next steps:")
    print("1. Follow the GOOGLE_CLOUD_DEPLOYMENT.md guide")
    print("2. Set up your Google Cloud project")
    print("3. Configure environment variables in app.yaml")
    print("4. Deploy with: gcloud app deploy")
    
    return True

def run_live_test():
    """Run a live server test"""
    print("\n🔴 OPTIONAL: Live Server Test")
    print("This will start a local server to test the application")
    
    response = input("Run live test? (y/N): ").lower().strip()
    if response != 'y':
        return True
    
    print("\nStarting test server...")
    
    # Start server in background
    import subprocess
    import time
    
    # Kill any existing process on port 8080
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], capture_output=True)
        else:  # Unix
            subprocess.run(['pkill', '-f', 'python.*main.py'], capture_output=True)
    except:
        pass
    
    # Start server
    server_process = subprocess.Popen([sys.executable, 'main.py'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE)
    
    # Wait for server to start
    time.sleep(3)
    
    try:
        # Test server
        response = requests.get('http://127.0.0.1:8080', timeout=5)
        if response.status_code in [200, 302]:
            print("✅ Live server test passed!")
            result = True
        else:
            print(f"❌ Live server test failed: {response.status_code}")
            result = False
    except Exception as e:
        print(f"❌ Live server test failed: {e}")
        result = False
    finally:
        # Stop server
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
    
    return result

if __name__ == "__main__":
    print("🚀 Google Cloud Pre-Deployment Test")
    
    if run_tests():
        run_live_test()
        print("\n🎯 Your application is ready for Google Cloud deployment!")
        print("📖 See GOOGLE_CLOUD_DEPLOYMENT.md for deployment instructions")
    else:
        print("\n❌ Some tests failed. Please fix the issues before deploying.")
        sys.exit(1)
