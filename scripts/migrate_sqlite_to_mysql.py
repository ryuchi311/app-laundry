"""One-shot migration: copy data from local SQLite `instance/laundry.db` into
the configured SQLAlchemy database (via app's DATABASE_URL).

Usage: run inside the project with your .env set (DATABASE_URL points to MySQL)

This script:
- Loads the Flask app (so SQLAlchemy models are available)
- Connects to the source SQLite DB using sqlite3
- For each table, selects rows and inserts into destination using SQLAlchemy

Caveats:
- It attempts to preserve primary keys where possible.
- It performs inserts in an order that respects FK dependencies (users, customers, services, etc.).
- Run only once and review logs. Backup the destination DB first!
"""

import os
import sqlite3
import sys
from datetime import datetime, date

# Ensure app package import works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import (
    User,
    Customer,
    Service,
    Laundry,
    LaundryAuditLog,
    LaundryStatusHistory,
    InventoryCategory,
    InventoryItem,
    StockMovement,
    ExpenseCategory,
    Expense,
    SalesReport,
    LoyaltyProgram,
    CustomerLoyalty,
    LoyaltyTransaction,
    SMSSettings,
)

SOURCE_DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'laundry.db'))

# Order matters for foreign keys
TABLE_ORDER = [
    'userdb',
    'customer',
    'service',
    'inventory_category',
    'inventory_item',
    'stock_movement',
    'expense_category',
    'expense',
    'sales_report',
    'loyalty_program',
    'customer_loyalty',
    'loyalty_transaction',
    'sms_settings',
    'laundry',
    'laundry_audit_log',
    'laundry_status_history',
    'sms_settings_profile',
    'notification',
    'export_audit',
    'dashboard_widget',
]

# Map table names to SQLAlchemy models and a simple row->model function
TABLE_MODEL_MAP = {
    'userdb': (User, None),
    'customer': (Customer, None),
    'service': (Service, None),
    'laundry': (Laundry, None),
    'laundry_audit_log': (LaundryAuditLog, None),
    'laundry_status_history': (LaundryStatusHistory, None),
    'inventory_category': (InventoryCategory, None),
    'inventory_item': (InventoryItem, None),
    'stock_movement': (StockMovement, None),
    'expense_category': (ExpenseCategory, None),
    'expense': (Expense, None),
    'sales_report': (SalesReport, None),
    'loyalty_program': (LoyaltyProgram, None),
    'customer_loyalty': (CustomerLoyalty, None),
    'loyalty_transaction': (LoyaltyTransaction, None),
    'sms_settings': (SMSSettings, None),
}


def row_to_kwargs(cols, row):
    return {cols[i]: row[i] for i in range(len(cols))}


def coerce_value(v):
    """Convert SQLite string timestamps/dates to Python datetime/date objects
    so SQLAlchemy DateTime/Date columns accept them.
    """
    if v is None:
        return None
    # sqlite3 may return bytes for BLOBs; leave non-strs alone
    if not isinstance(v, str):
        return v
    s = v.strip()
    if s == "":
        return None
    # Try datetime first (YYYY-MM-DD HH:MM:SS[.ffffff])
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # Try date (YYYY-MM-DD)
    try:
        return date.fromisoformat(s)
    except Exception:
        pass
    return s


def main(dry_run=True):
    if dry_run:
        print('DRY RUN: no changes will be written. Set dry_run=False to perform migration.')

    if not os.path.exists(SOURCE_DB):
        print('Source SQLite DB not found at', SOURCE_DB)
        return

    app = create_app()
    # Ensure destination DB is reachable
    with app.app_context():
        from sqlalchemy import text
        from sqlalchemy import insert as sa_insert
        try:
            # Use session.execute for SQLAlchemy 2.x compatibility
            db.session.execute(text('SELECT 1'))
        except Exception as e:
            print('Destination DB not reachable:', e)
            return

        src_conn = sqlite3.connect(SOURCE_DB)
        src_conn.row_factory = sqlite3.Row
        cursor = src_conn.cursor()

        # Temporarily disable foreign key checks for faster bulk insert and to allow
        # ordered inserts without strict FK enforcement. We'll re-enable afterwards.
        try:
            db.session.execute(text('SET FOREIGN_KEY_CHECKS=0'))
        except Exception:
            pass

        for table in TABLE_ORDER:
            if table not in TABLE_MODEL_MAP:
                print('Skipping unmapped table', table)
                continue
            model, _ = TABLE_MODEL_MAP[table]
            print('\nProcessing table', table)
            cursor.execute(f'SELECT * FROM {table}')
            rows = cursor.fetchall()
            print(f'  {len(rows)} rows')
            for r in rows:
                cols = r.keys()
                data = row_to_kwargs(cols, r)
                # Remove sqlite internal rowid if present
                data.pop('rowid', None)
                # Prepare insert values filtered to actual table columns
                cols_set = {c.name for c in model.__table__.columns}
                insert_values = {}
                for k, v in data.items():
                    if k in cols_set:
                        insert_values[k] = coerce_value(v)

                if dry_run:
                    print('   would insert:', {k: insert_values.get(k) for k in insert_values.keys() if k in ('id', 'laundry_id')})
                    continue

                # Use core INSERT IGNORE to skip duplicates (MySQL) and avoid ORM init
                try:
                    ins = sa_insert(model.__table__).prefix_with('IGNORE').values(**insert_values)
                    db.session.execute(ins)
                except Exception as exc:
                    print('   core insert failed for row', data.get('id'), exc)
                    # Rollback this transaction so we can continue with next table
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
            if not dry_run:
                try:
                    db.session.commit()
                    print('  committed')
                except Exception as e:
                    print('  commit failed for table', table, e)
                    db.session.rollback()
        src_conn.close()
    print('\nDone')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate SQLite to SQLAlchemy destination')
    parser.add_argument('--apply', action='store_true', help='Apply changes to destination DB')
    args = parser.parse_args()

    main(dry_run=not args.apply)
