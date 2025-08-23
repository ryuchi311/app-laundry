"""Filter suspicious phone changes for manual review.
Reads: instance/phone_changes.csv
Writes: instance/phone_changes_suspect.csv (id, full_name, old_phone, new_phone, reason)
"""
import csv
import os
import re

WORKDIR = os.path.dirname(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(WORKDIR, 'instance')
IN_CSV = os.path.join(INSTANCE_DIR, 'phone_changes.csv')
OUT_CSV = os.path.join(INSTANCE_DIR, 'phone_changes_suspect.csv')

if not os.path.exists(IN_CSV):
    print('Input CSV not found:', IN_CSV)
    raise SystemExit(1)

ph_pattern = re.compile(r'^(?:\+63|63|0?9)\d{7,10}$')
country_code_re = re.compile(r'^\+?(\d{1,3})')

suspects = []
with open(IN_CSV, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f)
    for row in r:
        old = (row.get('old_phone') or '').strip()
        new = (row.get('new_phone') or '').strip()
        reason_parts = []
        # quick normalization for pattern match
        old_digits = re.sub(r'[^\d+]', '', old)
        # Check if old looks PH-like
        if not (old.startswith('+63') or old.startswith('63') or old.startswith('09') or re.match(r'^9\d{9}$', re.sub(r'\D','', old))):
            reason_parts.append('old_not_obviously_PH')
        # Check if new has non-PH country code
        m_new = country_code_re.match(new)
        m_old = country_code_re.match(old)
        cc_new = m_new.group(1) if m_new else None
        cc_old = m_old.group(1) if m_old else None
        if cc_new and cc_new != '63':
            reason_parts.append(f'new_cc_{cc_new}')
        # Flag if new contains extension markers
        if 'x' in new or 'ext' in new.lower() or 'x' in new:
            reason_parts.append('new_has_extension')
        if reason_parts:
            suspects.append((row['id'], row['full_name'], old, new, ';'.join(reason_parts)))

with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['id', 'full_name', 'old_phone', 'new_phone', 'reason'])
    for s in suspects:
        w.writerow(s)

print('Wrote', len(suspects), 'suspects to', OUT_CSV)
