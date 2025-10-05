# Supabase Quick Start & Testing Guide

This guide will help you test your Supabase connection and get your application running.

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `psycopg2-binary` - PostgreSQL driver
- `supabase` - Supabase Python client (optional)
- All other existing dependencies

### Step 2: Configure Environment

Edit your `.env` file with your Supabase credentials:

```env
# Required: Database Connection
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

# Optional: Supabase API (for advanced features)
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=your-anon-key-here

# Keep your other settings
SECRET_KEY=your_secret_key
SEMAPHORE_API_KEY=your_api_key
SEMAPHORE_SENDER_NAME=ACCIOWash
```

**Get your credentials from:**
- Supabase Dashboard → Settings → Database → Connection string
- Supabase Dashboard → Settings → API

### Step 3: Test Database Connection

Create a simple test script `test_supabase_connection.py`:

```python
#!/usr/bin/env python3
"""Test Supabase database connection"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not found in .env file")
    exit(1)

print("Testing Supabase connection...")
print(f"Connecting to: {DATABASE_URL[:50]}...")

try:
    # Create engine
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "connect_timeout": 10,
            "sslmode": "prefer",
        },
        pool_pre_ping=True,
    )
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"\n✅ SUCCESS! Connected to PostgreSQL")
        print(f"Version: {version}")
        
        # Test database info
        result = conn.execute(text("SELECT current_database(), current_user"))
        db_info = result.fetchone()
        print(f"Database: {db_info[0]}")
        print(f"User: {db_info[1]}")
        
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"\n📊 Existing tables ({len(tables)}):")
            for table in tables:
                print(f"  - {table}")
        else:
            print("\n📊 No tables found (fresh database)")
    
    engine.dispose()
    print("\n✅ Connection test passed!")
    print("\nNext step: Create tables with:")
    print("  python -c \"from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all(); print('Tables created!')\"")
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("  1. Check your DATABASE_URL in .env")
    print("  2. Verify your Supabase project is active")
    print("  3. Ensure you replaced [project-ref] and [password]")
    print("  4. Check if psycopg2-binary is installed: pip install psycopg2-binary")
    exit(1)
```

Run it:

```bash
python test_supabase_connection.py
```

**Expected output:**
```
✅ SUCCESS! Connected to PostgreSQL
Version: PostgreSQL 15.x ...
Database: postgres
User: postgres.xxx
```

### Step 4: Create Database Tables

```bash
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all(); print('✅ Tables created!')"
```

This will create all tables defined in your `app/models.py`.

### Step 5: Disable Row Level Security (RLS)

Supabase enables RLS by default. For Flask app with its own authentication, disable it:

**Option A: Using SQL Editor in Supabase Dashboard**

1. Go to SQL Editor in Supabase dashboard
2. Create a new query
3. Paste and run:

```sql
-- Disable RLS on all tables
DO $$ 
DECLARE 
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'ALTER TABLE ' || quote_ident(r.tablename) || ' DISABLE ROW LEVEL SECURITY';
    END LOOP;
END $$;

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Show result
SELECT tablename, 
       relrowsecurity as rls_enabled
FROM pg_tables t
JOIN pg_class c ON t.tablename = c.relname
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Option B: Using Python Script**

Create `disable_rls.py`:

```python
#!/usr/bin/env python3
"""Disable Row Level Security on all tables"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get all tables
    result = conn.execute(text("""
        SELECT tablename FROM pg_tables WHERE schemaname = 'public'
    """))
    tables = [row[0] for row in result.fetchall()]
    
    print(f"Disabling RLS on {len(tables)} tables...")
    
    for table in tables:
        try:
            conn.execute(text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))
            conn.commit()
            print(f"  ✓ {table}")
        except Exception as e:
            print(f"  ✗ {table}: {e}")
    
    # Grant permissions
    conn.execute(text("GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated"))
    conn.execute(text("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated"))
    conn.commit()
    
    print("\n✅ RLS disabled on all tables!")

engine.dispose()
```

Run it:

```bash
python disable_rls.py
```

### Step 6: Create First User (Super Admin)

```bash
python -c "
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check if user exists
    if User.query.filter_by(email='admin@acciowash.com').first():
        print('User already exists')
    else:
        user = User()
        user.email = 'admin@acciowash.com'
        user.full_name = 'Super Admin'
        user.password = generate_password_hash('Admin123!', method='pbkdf2:sha256')
        user.role = 'super_admin'
        user.is_active = True
        db.session.add(user)
        db.session.commit()
        print('✅ Super admin created!')
        print('Email: admin@acciowash.com')
        print('Password: Admin123!')
        print('⚠️  Change this password after first login!')
"
```

### Step 7: Run Your Application

```bash
python main.py
```

Or with Gunicorn (production):

```bash
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:8080 main:app
```

### Step 8: Test Login

1. Open browser: `http://localhost:8080`
2. Login with:
   - Email: `admin@acciowash.com`
   - Password: `Admin123!`
3. Change your password immediately!

---

## Detailed Testing Checklist

### ✅ Connection Tests

- [ ] Database connection successful
- [ ] Can create tables
- [ ] Can insert data
- [ ] Can query data
- [ ] SSL connection working

### ✅ Application Tests

- [ ] Application starts without errors
- [ ] Login page loads
- [ ] Can log in with admin account
- [ ] Dashboard loads
- [ ] Can view customers
- [ ] Can create new customer
- [ ] Can create laundry order
- [ ] Can update order status
- [ ] Can view reports
- [ ] SMS notifications work (if configured)

### ✅ Performance Tests

- [ ] Page load times acceptable
- [ ] Complex queries perform well
- [ ] No connection pool exhaustion
- [ ] Real-time updates work (if enabled)

---

## Testing Individual Features

### Test Customer Creation

```python
from app import create_app, db
from app.models import Customer

app = create_app()
with app.app_context():
    customer = Customer()
    customer.full_name = "Test Customer"
    customer.phone = "09123456789"
    customer.email = "test@example.com"
    db.session.add(customer)
    db.session.commit()
    print(f"✅ Customer created with ID: {customer.id}")
```

### Test Laundry Order

```python
from app import create_app, db
from app.models import Customer, Laundry
from datetime import datetime

app = create_app()
with app.app_context():
    # Get a customer
    customer = Customer.query.first()
    if not customer:
        print("❌ No customers found. Create a customer first.")
    else:
        order = Laundry()
        order.customer_id = customer.id
        order.status = "pending"
        order.date_created = datetime.utcnow()
        order.total = 100.0
        db.session.add(order)
        db.session.commit()
        print(f"✅ Order created with ID: {order.id}")
```

### Test Query Performance

```python
from app import create_app, db
from app.models import Laundry
import time

app = create_app()
with app.app_context():
    start = time.time()
    orders = Laundry.query.limit(100).all()
    elapsed = time.time() - start
    print(f"✅ Queried {len(orders)} orders in {elapsed:.3f}s")
```

---

## Monitoring & Debugging

### View Database Logs

1. Go to Supabase Dashboard
2. Click **Logs** in sidebar
3. Select **Database** logs
4. Filter by time range

### Check Connection Pool

```python
from app import create_app, db

app = create_app()
with app.app_context():
    pool = db.engine.pool
    print(f"Pool size: {pool.size()}")
    print(f"Checked out: {pool.checkedout()}")
    print(f"Overflow: {pool.overflow()}")
```

### Monitor Query Performance

Enable SQLAlchemy logging in your `.env`:

```env
SQLALCHEMY_ECHO=1
```

This will print all SQL queries to console.

### Check Supabase Dashboard

- **Database Health**: Dashboard → Reports
- **Query Performance**: Dashboard → Database → Query Performance
- **Connection Count**: Dashboard → Reports → Database
- **Disk Usage**: Dashboard → Reports → Database

---

## Troubleshooting

### Issue: "Connection refused"

**Check:**
- Is your Supabase project active?
- Are you using the correct port (6543 for pooler)?
- Is `DATABASE_URL` correct in `.env`?

**Solution:**
```bash
# Test with psql
psql "postgresql://postgres.[project]:[pass]@aws-0-region.pooler.supabase.com:6543/postgres"
```

### Issue: "SSL connection required"

**Solution:** Add to your `.env`:
```env
DATABASE_URL=postgresql://...?sslmode=require
```

### Issue: "Too many connections"

**Solution:** Reduce pool size in `app/__init__.py`:
```python
app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"] = 3
app.config["SQLALCHEMY_ENGINE_OPTIONS"]["max_overflow"] = 5
```

### Issue: "Permission denied for table"

**Solution:** Disable RLS (see Step 5 above)

### Issue: "Table does not exist"

**Solution:** Create tables:
```bash
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
```

### Issue: Slow queries

**Solution:** Add indexes:
```sql
CREATE INDEX idx_customer_phone ON customer(phone);
CREATE INDEX idx_laundry_status ON laundry(status);
CREATE INDEX idx_laundry_customer ON laundry(customer_id);
```

---

## Performance Tips

### 1. Use Connection Pooler

Always use port **6543** (pooler), not 5432 (direct):
```
postgresql://...pooler.supabase.com:6543/postgres
```

### 2. Enable Connection Pre-Ping

Already configured in `app/__init__.py`:
```python
"pool_pre_ping": True
```

### 3. Set Appropriate Pool Size

For most apps:
```python
"pool_size": 5,
"max_overflow": 10,
```

For high-traffic:
```python
"pool_size": 10,
"max_overflow": 20,
```

### 4. Use Indexes

Add indexes for commonly queried columns:
```sql
CREATE INDEX idx_customer_search ON customer USING gin(to_tsvector('english', full_name));
```

### 5. Enable Query Caching

For read-heavy operations, consider Redis caching.

---

## Next Steps After Testing

### 1. Migrate Production Data

Follow the migration guide in `SUPABASE_MIGRATION_GUIDE.md`

### 2. Set Up Backups

- Supabase Free: Daily backups (7-day retention)
- Configure custom backups if needed

### 3. Set Up Monitoring

- Enable monitoring in Supabase dashboard
- Set up email alerts for errors
- Monitor connection pool usage

### 4. Optimize Queries

Use `EXPLAIN ANALYZE` to identify slow queries:
```sql
EXPLAIN ANALYZE
SELECT * FROM laundry WHERE status = 'pending';
```

### 5. Explore Advanced Features

- Real-time subscriptions (see `app/supabase_helper.py`)
- Full-text search
- PostGIS for location features
- Custom PostgreSQL functions

---

## Success Indicators

Your migration is successful when:

✅ All tests pass  
✅ Application runs without errors  
✅ Users can login  
✅ CRUD operations work  
✅ Reports generate correctly  
✅ SMS notifications send  
✅ Performance is acceptable  
✅ No connection errors in logs  

---

## Getting Help

If you encounter issues:

1. **Check Supabase Status**: [status.supabase.com](https://status.supabase.com)
2. **Review Logs**: Supabase Dashboard → Logs
3. **Supabase Discord**: [discord.supabase.com](https://discord.supabase.com)
4. **Documentation**: [supabase.com/docs](https://supabase.com/docs)

---

## Additional Resources

- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/14/dialects/postgresql.html)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Connection Pooling Best Practices](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

Good luck with your Supabase migration! 🚀
