import sqlite3
from datetime import datetime

def backfill_audit_logs():
    """
    Create audit log entries for existing orders that were created before 
    the audit logging system was implemented.
    """
    conn = sqlite3.connect('instance/laundry.db')
    cursor = conn.cursor()
    
    print("Backfilling audit logs for existing orders...")
    
    # Get all orders that don't have any audit log entries
    cursor.execute('''
        SELECT DISTINCT o.order_id, o.date_received 
        FROM [order] o 
        LEFT JOIN order_audit_log al ON o.order_id = al.order_id 
        WHERE al.order_id IS NULL
    ''')
    
    orders_without_audit = cursor.fetchall()
    
    if not orders_without_audit:
        print("✓ All orders already have audit log entries.")
        conn.close()
        return
    
    print(f"Found {len(orders_without_audit)} orders without audit logs.")
    
    # Get the first user ID for attribution (since we don't know who originally created the order)
    cursor.execute('SELECT id FROM user LIMIT 1')
    user_result = cursor.fetchone()
    
    if not user_result:
        print("✗ No users found in database. Cannot backfill audit logs.")
        conn.close()
        return
    
    first_user_id = user_result[0]
    
    # Create CREATED audit log entries for orders without audit history
    for order_id, date_received in orders_without_audit:
        cursor.execute('''
            INSERT INTO order_audit_log 
            (order_id, action, field_changed, old_value, new_value, changed_by, changed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_id,
            'CREATED',
            None,
            None,
            'Order created (backfilled entry)',
            first_user_id,
            date_received  # Use the original date_received as the audit timestamp
        ))
        print(f"✓ Created audit log entry for order {order_id}")
    
    conn.commit()
    conn.close()
    print(f"Successfully backfilled audit logs for {len(orders_without_audit)} orders!")

if __name__ == '__main__':
    backfill_audit_logs()
