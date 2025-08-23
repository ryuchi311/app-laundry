"""Generate CSV of phone changes between current DB and a backup.

Output: instance/phone_changes.csv with columns: id, full_name, old_phone, new_phone
"""
import sqlite3
import csv
import os
from datetime import datetime

WORKDIR = os.path.dirname(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(WORKDIR, 'instance')
CURRENT_DB = os.path.join(INSTANCE_DIR, 'laundry.db')
# pick latest .bak by modification time
backups = [os.path.join(INSTANCE_DIR, f) for f in os.listdir(INSTANCE_DIR) if f.endswith('.bak')]
if not backups:
    print('No backups found in instance/; aborting')
    raise SystemExit(1)
backup = max(backups, key=lambda p: os.path.getmtime(p))
print('Using backup:', os.path.basename(backup))

def rows_from_db(path):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('SELECT id, full_name, phone FROM customer')
    rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    conn.close()
    return rows

old = rows_from_db(backup)
new = rows_from_db(CURRENT_DB)

changed = []
for cid, (name_old, phone_old) in old.items():
    if cid in new:
        name_new, phone_new = new[cid]
        if (phone_old or '').strip() != (phone_new or '').strip():
            changed.append((cid, name_new or name_old, phone_old or '', phone_new or ''))

out_csv = os.path.join(INSTANCE_DIR, 'phone_changes.csv')
with open(out_csv, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['id', 'full_name', 'old_phone', 'new_phone'])
    for row in changed:
        w.writerow(row)

print(f'Wrote {len(changed)} changes to', out_csv)
