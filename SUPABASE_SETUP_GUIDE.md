# Supabase Setup Guide for Laundry App

This guide will help you migrate your laundry application from MySQL to Supabase (PostgreSQL).

## What is Supabase?

Supabase is an open-source Firebase alternative that provides:
- **PostgreSQL Database** - A powerful relational database
- **Auto-generated REST APIs** - Instantly access your data via REST
- **Real-time subscriptions** - Live updates when data changes
- **Authentication** - Built-in user management (optional to use)
- **Storage** - File storage with CDN
- **Row Level Security** - Fine-grained access control

For your Flask app, we'll primarily use the PostgreSQL database, but you can optionally leverage other features later.

---

## Step 1: Create a Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"** or **"Sign In"**
3. Sign up using:
   - GitHub account (recommended)
   - Email and password

---

## Step 2: Create a New Project

1. After signing in, click **"New Project"**
2. Fill in the project details:
   - **Organization**: Select or create an organization
   - **Project Name**: `acciowash-db` (or any name you prefer)
   - **Database Password**: Create a **strong password** and **SAVE IT SECURELY**
     - This password is used for direct database connections
     - You cannot recover it if lost
   - **Region**: Choose the region closest to your users
     - For Philippines: `Southeast Asia (Singapore)`
     - For US: `US East (N. Virginia)` or `US West (Oregon)`
   - **Pricing Plan**: Start with **Free tier** (500 MB database, 50,000 monthly active users)

3. Click **"Create new project"**
4. Wait 1-2 minutes for the project to be provisioned

---

## Step 3: Get Your Database Connection String

Once your project is ready:

### Method 1: Direct Connection (Recommended for Flask)

1. In your Supabase dashboard, click **Settings** (gear icon in sidebar)
2. Click **Database** in the left menu
3. Scroll to **"Connection string"** section
4. Select **"URI"** tab
5. Choose **"Transaction"** mode (best for web apps)
6. Copy the connection string - it looks like:
   ```
   postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
7. **IMPORTANT**: Replace `[YOUR-PASSWORD]` with the database password you created

### Method 2: Connection Parameters (Alternative)

If you need individual parameters, you'll find:
- **Host**: `aws-0-[region].pooler.supabase.com`
- **Port**: `6543` (pooler) or `5432` (direct)
- **Database**: `postgres`
- **User**: `postgres.[project-ref]`
- **Password**: Your database password

---

## Step 4: Enable Necessary Extensions (Optional but Recommended)

Supabase comes with many PostgreSQL extensions. For your app, you might want:

1. Go to **Database** → **Extensions** in the Supabase dashboard
2. Enable these extensions if needed:
   - `uuid-ossp` - For generating UUIDs (if you want to use UUIDs instead of integers)
   - `pg_trgm` - For better text search performance
   - `unaccent` - For accent-insensitive searches

For now, the default extensions should be sufficient.

---

## Step 5: Understand Supabase Database Access

Supabase provides **two ways** to connect:

### 1. **Connection Pooler** (Recommended for Web Apps)
- **Port**: `6543`
- Uses PgBouncer for connection pooling
- Better for serverless/cloud deployments
- Handles many concurrent connections
- **Use this for your Flask app**

### 2. **Direct Connection**
- **Port**: `5432`
- Direct PostgreSQL connection
- Better for migrations and admin tasks
- Limited to 60 concurrent connections (free tier)

**For your Flask app, use the pooler connection (port 6543) in transaction mode.**

---

## Step 6: Save Your Credentials Securely

You'll need these credentials for your `.env` file:

1. **Supabase URL** (API URL): Found in **Settings** → **API**
2. **Supabase Anon Key**: Found in **Settings** → **API** (for API access, optional)
3. **Database Connection String**: From Step 3 above
4. **Database Password**: The password you created

**Example of what you'll configure:**

```env
# Supabase Database Connection (PostgreSQL)
DATABASE_URL=postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres

# Optional: Supabase API Access (if you want to use Supabase client)
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_KEY=your-anon-key-here
```

---

## Step 7: Explore the Supabase Dashboard

### Table Editor
- Go to **Table Editor** in the sidebar
- After migration, you'll see all your tables here
- You can browse, edit, and query data visually
- Add indexes, modify columns, etc.

### SQL Editor
- Go to **SQL Editor** in the sidebar
- Run custom SQL queries
- Useful for data migration and testing

### Database
- Go to **Database** in the sidebar
- View tables, functions, extensions, roles
- Monitor database size and connections

### API Documentation
- Supabase auto-generates REST API documentation
- Go to **API Docs** in the sidebar
- See auto-generated endpoints for each table
- (Optional - you can keep using SQLAlchemy)

---

## Step 8: Connection Limits & Best Practices

### Free Tier Limits
- **Direct connections**: Max 60 concurrent
- **Pooler connections**: Much higher (500+)
- **Database size**: 500 MB
- **Bandwidth**: 2 GB per month

### Best Practices
1. **Always use the pooler** (port 6543) for your Flask app
2. **Set connection pool limits** in SQLAlchemy:
   ```python
   pool_size=5,
   max_overflow=10,
   pool_pre_ping=True,
   pool_recycle=300
   ```
3. **Use environment variables** for credentials (never commit them)
4. **Enable SSL** (Supabase enforces SSL by default)
5. **Monitor usage** in Supabase dashboard under **Reports**

---

## Step 9: Security Considerations

### Row Level Security (RLS)
- Supabase has RLS enabled by default on new tables
- For Flask/SQLAlchemy access, you have two options:
  1. **Disable RLS** on tables (easier, uses your Flask auth)
  2. **Configure RLS policies** (more secure, uses Supabase auth)

**For your app** (using Flask-Login), you should:
1. After migration, disable RLS on your tables:
   ```sql
   ALTER TABLE userdb DISABLE ROW LEVEL SECURITY;
   ALTER TABLE customer DISABLE ROW LEVEL SECURITY;
   -- Repeat for all tables
   ```

Or keep RLS enabled and add permissive policies:
```sql
CREATE POLICY "Allow all for authenticated users" ON userdb
FOR ALL USING (true) WITH CHECK (true);
```

We'll handle this in the migration script.

---

## Step 10: Next Steps

After completing this setup:

1. ✅ You have a Supabase project
2. ✅ You have your database connection string
3. ✅ You understand the connection methods

**Next**: Update your Flask app configuration to use Supabase (covered in the migration steps).

---

## Troubleshooting

### "Connection refused"
- Check if you're using the correct port (6543 for pooler)
- Verify your IP is allowed (Supabase free tier is open to all by default)

### "Password authentication failed"
- Double-check your database password
- Make sure you replaced `[YOUR-PASSWORD]` in the connection string

### "Too many connections"
- Use the pooler (port 6543) instead of direct connection
- Reduce pool_size in SQLAlchemy configuration

### "SSL required"
- Supabase requires SSL connections
- Add `?sslmode=require` to your connection string if needed
- Most PostgreSQL drivers handle this automatically

---

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL vs MySQL Differences](https://supabase.com/docs/guides/database/postgres-vs-mysql)
- [Connection Pooling Best Practices](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)

---

## Need Help?

- Supabase Discord: [https://discord.supabase.com](https://discord.supabase.com)
- Supabase Discussions: [https://github.com/supabase/supabase/discussions](https://github.com/supabase/supabase/discussions)
- Community support is very active and helpful!
