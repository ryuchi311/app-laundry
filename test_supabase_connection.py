#!/usr/bin/env python3
"""
Quick Supabase Connection Test
Run this to verify your Supabase database connection is working.

Usage:
    python test_supabase_connection.py
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection and display info"""
    
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not found in .env file")
        print("\nPlease add your Supabase connection string to .env:")
        print("DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres")
        return False
    
    # Hide password in output
    display_url = DATABASE_URL[:50] + "..." if len(DATABASE_URL) > 50 else DATABASE_URL
    if "@" in display_url:
        parts = display_url.split("@")
        if ":" in parts[0]:
            user_parts = parts[0].split(":")
            display_url = f"{user_parts[0]}:****@{parts[1] if len(parts) > 1 else ''}"
    
    print("=" * 60)
    print("SUPABASE CONNECTION TEST")
    print("=" * 60)
    print(f"\nConnecting to: {display_url}")
    
    try:
        # Detect database type
        db_type = "Unknown"
        if "postgresql" in DATABASE_URL.lower() or "postgres" in DATABASE_URL.lower():
            db_type = "PostgreSQL (Supabase)"
        elif "mysql" in DATABASE_URL.lower():
            db_type = "MySQL (Legacy)"
        
        print(f"Database Type: {db_type}")
        
        # Create engine with proper settings
        connect_args = {"connect_timeout": 10}
        if "postgresql" in DATABASE_URL.lower() or "postgres" in DATABASE_URL.lower():
            connect_args["sslmode"] = "prefer"
        
        engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        
        print("\n🔄 Connecting...")
        
        # Test connection
        with engine.connect() as conn:
            # Get version
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            
            # Get database info
            result = conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            
            print("\n✅ SUCCESS! Connected to database\n")
            print("-" * 60)
            print(f"Version: {version[:80]}...")
            print(f"Database: {db_info[0]}")
            print(f"User: {db_info[1]}")
            print("-" * 60)
            
            # Check for existing tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"\n📊 Found {len(tables)} existing tables:")
                for i, table in enumerate(tables, 1):
                    # Get row count for each table
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = count_result.fetchone()[0]
                        print(f"  {i:2d}. {table:<30} ({count:,} rows)")
                    except Exception:
                        print(f"  {i:2d}. {table}")
            else:
                print("\n📊 No tables found (fresh database)")
                print("\n💡 Next step: Create tables with:")
                print('   python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all(); print(\'✅ Tables created!\')"')
        
        engine.dispose()
        
        print("\n" + "=" * 60)
        print("✅ CONNECTION TEST PASSED!")
        print("=" * 60)
        
        if "postgresql" in DATABASE_URL.lower():
            print("\n📝 Next Steps for Supabase:")
            print("   1. Create tables (see command above)")
            print("   2. Disable Row Level Security (see SUPABASE_TESTING_GUIDE.md)")
            print("   3. Create first admin user")
            print("   4. Start your application: python main.py")
            print("\n📚 Full guide: SUPABASE_TESTING_GUIDE.md")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        if "psycopg2" in str(e):
            print("\n💡 Install PostgreSQL driver:")
            print("   pip install psycopg2-binary")
        elif "pymysql" in str(e):
            print("\n💡 Install MySQL driver:")
            print("   pip install pymysql")
        else:
            print("\n💡 Install dependencies:")
            print("   pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\n🔍 Troubleshooting:")
        print("   1. Check your DATABASE_URL in .env file")
        print("   2. Verify your Supabase project is active (https://supabase.com)")
        print("   3. Ensure you replaced [project-ref] and [password] with actual values")
        print("   4. Check if the correct driver is installed:")
        
        if "postgresql" in DATABASE_URL.lower():
            print("      For PostgreSQL: pip install psycopg2-binary")
        elif "mysql" in DATABASE_URL.lower():
            print("      For MySQL: pip install pymysql")
        
        print("\n📚 Full troubleshooting guide: SUPABASE_TESTING_GUIDE.md")
        return False


def check_environment():
    """Check if all required environment variables are set"""
    print("\n" + "=" * 60)
    print("ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 60 + "\n")
    
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    optional_vars = ["SUPABASE_URL", "SUPABASE_KEY", "SEMAPHORE_API_KEY", "MAIL_USERNAME"]
    
    print("Required Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var:<20} = {masked}")
        else:
            print(f"  ❌ {var:<20} = NOT SET")
    
    print("\nOptional Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var:<20} = {masked}")
        else:
            print(f"  ⚪ {var:<20} = not set")


if __name__ == "__main__":
    print("\n")
    
    # Check environment
    check_environment()
    
    # Test connection
    success = test_connection()
    
    print("\n")
    sys.exit(0 if success else 1)
