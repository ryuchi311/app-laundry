# MySQL to Supabase Migration Guide

This guide will help you migrate your existing data from MySQL to Supabase (PostgreSQL).

## Prerequisites

Before starting, ensure you have:
- ✅ Completed the Supabase setup (see `SUPABASE_SETUP_GUIDE.md`)
- ✅ Your Supabase connection string
- ✅ Access to your current MySQL database
- ✅ Python 3.8+ installed
- ✅ Updated dependencies installed: `pip install -r requirements.txt`

---

## Migration Approach

We'll use one of these methods:

1. **Method 1: pgloader (Recommended)** - Fastest, automatic schema conversion
2. **Method 2: Python Script** - More control, good for data transformation
3. **Method 3: Export/Import SQL** - Manual but reliable
4. **Method 4: Fresh Start** - Start with empty database (if data is not critical)

---

## Method 1: Using pgloader (Recommended)

pgloader is a powerful tool that migrates data from MySQL to PostgreSQL automatically.

### Step 1: Install pgloader

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install pgloader
```

**On macOS:**
```bash
brew install pgloader
```

**On Windows:**
Use Docker:
```bash
docker pull dimitri/pgloader
```

### Step 2: Create Migration Config File

Create `mysql_to_supabase.load`:

```
LOAD DATABASE
     FROM mysql://u170166215_chicago311:RMXXl0bNr$S2mz@31.220.110.101:3306/u170166215_acciowash_db
     INTO postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres

WITH include drop, create tables, create indexes, reset sequences,
     workers = 8, concurrency = 1,
     multiple readers per thread, rows per range = 50000

SET PostgreSQL PARAMETERS
     maintenance_work_mem to '128MB',
     work_mem to '12MB'

CAST type datetime to timestamptz
                  drop default drop not null using zero-dates-to-null,
     type date drop not null drop default using zero-dates-to-null,
     type tinyint to boolean using tinyint-to-boolean,
     type year to integer

BEFORE LOAD DO
  $$ DROP SCHEMA IF EXISTS public CASCADE; $$,
  $$ CREATE SCHEMA public; $$;
```

**Important**: Replace the connection strings with your actual credentials!

### Step 3: Run the Migration

```bash
pgloader mysql_to_supabase.load
```

This will:
- Drop existing tables in Supabase (if any)
- Create all tables with converted schemas
- Copy all data
- Create indexes
- Reset sequences

**Migration time**: Depends on data size. Usually ~1000 rows/second.

### Step 4: Verify Migration

After completion, pgloader will show a summary. Check for:
- All tables migrated
- Row counts match
- No errors

### Step 5: Fix Row Level Security (RLS)

Supabase enables RLS by default. Disable it for Flask app:

```sql
-- Connect to Supabase SQL Editor and run:

ALTER TABLE userdb DISABLE ROW LEVEL SECURITY;
ALTER TABLE customer DISABLE ROW LEVEL SECURITY;
ALTER TABLE laundry DISABLE ROW LEVEL SECURITY;
ALTER TABLE service DISABLE ROW LEVEL SECURITY;
ALTER TABLE laundry_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE inventory DISABLE ROW LEVEL SECURITY;
ALTER TABLE expenses DISABLE ROW LEVEL SECURITY;
ALTER TABLE business_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE sms_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE sms_settings_profile DISABLE ROW LEVEL SECURITY;
ALTER TABLE customer_loyalty DISABLE ROW LEVEL SECURITY;

-- Grant permissions to authenticated users
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
```

---

## Method 2: Python Migration Script

If pgloader is not available, use this Python script.

### Step 1: Create Migration Script

Create `scripts/migrate_mysql_to_supabase.py`:

```python
#!/usr/bin/env python3
"""
Migrate data from MySQL to Supabase (PostgreSQL)
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Source MySQL database
MYSQL_URL = "mysql+pymysql://u170166215_chicago311:RMXXl0bNr$S2mz@31.220.110.101:3306/u170166215_acciowash_db"

# Target Supabase database
SUPABASE_URL = os.getenv("DATABASE_URL")

if not SUPABASE_URL:
    print("Error: DATABASE_URL not set in .env file")
    sys.exit(1)

def migrate():
    print("Connecting to MySQL...")
    mysql_engine = create_engine(MYSQL_URL)
    mysql_meta = MetaData()
    mysql_meta.reflect(bind=mysql_engine)
    
    print("Connecting to Supabase...")
    pg_engine = create_engine(SUPABASE_URL)
    pg_meta = MetaData()
    
    print("Creating tables in Supabase...")
    # Use your Flask models to create tables
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from app import create_app, db
    
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Tables created!")
        
        print("Migrating data...")
        # Get table names
        inspector = inspect(mysql_engine)
        tables = inspector.get_table_names()
        
        for table_name in tables:
            print(f"Migrating table: {table_name}")
            
            # Reflect table from MySQL
            mysql_table = Table(table_name, mysql_meta, autoload_with=mysql_engine)
            
            # Read from MySQL
            with mysql_engine.connect() as mysql_conn:
                result = mysql_conn.execute(mysql_table.select())
                rows = result.fetchall()
                
                if not rows:
                    print(f"  No data in {table_name}")
                    continue
                
                print(f"  Found {len(rows)} rows")
                
                # Reflect table from PostgreSQL
                pg_table = Table(table_name, pg_meta, autoload_with=pg_engine)
                
                # Insert into PostgreSQL
                with pg_engine.begin() as pg_conn:
                    for row in rows:
                        # Convert row to dict
                        row_dict = dict(row._mapping)
                        pg_conn.execute(pg_table.insert().values(**row_dict))
                
                print(f"  ✓ Migrated {len(rows)} rows")
        
        print("\n✅ Migration complete!")
        print("\nNext steps:")
        print("1. Verify data in Supabase dashboard")
        print("2. Disable RLS on tables (see migration guide)")
        print("3. Test your application")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

### Step 2: Run Migration Script

```bash
python scripts/migrate_mysql_to_supabase.py
```

---

## Method 3: SQL Export/Import

### Step 1: Export from MySQL

```bash
mysqldump -h 31.220.110.101 -u u170166215_chicago311 -p u170166215_acciowash_db > backup.sql
```

### Step 2: Convert MySQL SQL to PostgreSQL

Use a tool like `mysql2psql` or manually edit:

**Common changes needed:**
- `AUTO_INCREMENT` → `SERIAL`
- `TINYINT(1)` → `BOOLEAN`
- Backticks (`) → Double quotes (")
- `ENGINE=InnoDB` → Remove
- `DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` → Use triggers

### Step 3: Import to Supabase

1. Go to Supabase SQL Editor
2. Paste your converted SQL
3. Execute

---

## Method 4: Fresh Start (No Migration)

If your current data is not critical:

### Step 1: Update .env

```env
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

### Step 2: Create Tables

```bash
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all(); print('Tables created!')"
```

### Step 3: Disable RLS

Run the SQL commands from Method 1, Step 5.

### Step 4: Start Fresh

Your app will create a new database. You can manually re-add critical data or start from scratch.

---

## Post-Migration Steps

### 1. Verify Data Integrity

```python
# Check record counts
from app import create_app, db
from app.models import User, Customer, Laundry, Service

app = create_app()
with app.app_context():
    print(f"Users: {User.query.count()}")
    print(f"Customers: {Customer.query.count()}")
    print(f"Laundry Orders: {Laundry.query.count()}")
    print(f"Services: {Service.query.count()}")
```

### 2. Test Critical Functions

- ✅ User login
- ✅ Create/edit customers
- ✅ Create laundry orders
- ✅ View reports
- ✅ SMS notifications

### 3. Update Indexes (Optional)

PostgreSQL may benefit from different indexes than MySQL:

```sql
-- Add commonly queried indexes
CREATE INDEX idx_customer_phone ON customer(phone);
CREATE INDEX idx_laundry_status ON laundry(status);
CREATE INDEX idx_laundry_date ON laundry(date_created);
CREATE INDEX idx_customer_active ON customer(is_active);
```

### 4. Enable Full-Text Search (Optional)

PostgreSQL has powerful full-text search:

```sql
-- Add GIN index for customer search
CREATE INDEX idx_customer_search ON customer USING gin(to_tsvector('english', full_name));
```

### 5. Optimize PostgreSQL Settings

In Supabase dashboard → Database → Configuration:

- Increase `shared_buffers` if needed
- Tune `effective_cache_size`
- Adjust `work_mem` for complex queries

---

## Rollback Plan

If something goes wrong:

1. **Keep your MySQL connection string** in `.env` (commented out)
2. **Take a Supabase snapshot** before migration
3. **Test thoroughly** on a staging environment first

To rollback:

```env
# Revert to MySQL
DATABASE_URL=mysql+pymysql://u170166215_chicago311:RMXXl0bNr$S2mz@31.220.110.101:3306/u170166215_acciowash_db
```

Then restart your app.

---

## Common Issues & Solutions

### Issue: "relation does not exist"

**Solution**: Ensure tables are created before data migration:
```bash
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
```

### Issue: "permission denied for table"

**Solution**: Disable RLS or add proper policies (see Method 1, Step 5)

### Issue: "too many connections"

**Solution**: Use connection pooler (port 6543) and reduce pool_size:
```python
app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"] = 3
app.config["SQLALCHEMY_ENGINE_OPTIONS"]["max_overflow"] = 5
```

### Issue: "SSL connection required"

**Solution**: Add SSL mode to connection string:
```
?sslmode=require
```

### Issue: Data type mismatches

**Solution**: PostgreSQL is stricter. Check:
- Boolean values (1/0 vs TRUE/FALSE)
- Date formats
- String encoding (use UTF-8)

---

## Performance Comparison

After migration, you may notice:

**Faster:**
- Complex queries with JOINs
- Full-text search
- JSON operations
- Analytics queries

**Similar:**
- Simple CRUD operations
- Primary key lookups

**Considerations:**
- PostgreSQL uses more memory
- Connection pooling is critical
- VACUUM and ANALYZE run automatically

---

## Next Steps

After successful migration:

1. ✅ Test all application features
2. ✅ Monitor Supabase dashboard for errors
3. ✅ Set up automated backups
4. ✅ Consider using Supabase real-time features
5. ✅ Explore Supabase Auth (optional)
6. ✅ Add monitoring and alerts

---

## Additional Resources

- [Supabase Migrating to Supabase](https://supabase.com/docs/guides/migrations)
- [pgloader Documentation](https://pgloader.readthedocs.io/)
- [PostgreSQL vs MySQL Differences](https://www.postgresql.org/docs/current/features.html)
- [SQLAlchemy PostgreSQL Dialect](https://docs.sqlalchemy.org/en/14/dialects/postgresql.html)

---

## Need Help?

If you encounter issues:
1. Check Supabase logs (Dashboard → Logs)
2. Review PostgreSQL logs (Dashboard → Database → Logs)
3. Ask in Supabase Discord
4. Check this project's documentation

Good luck with your migration! 🚀
