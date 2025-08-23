#!/usr/bin/env python3
"""Normalize customer phone numbers to +63XXXXXXXXXX format.

Backs up instance/laundry.db before making changes.
Only updates values that can be reasonably converted to Philippine mobile format.
"""
import os
import re
import shutil
import sys
from datetime import datetime

# Ensure project root is on sys.path when running this script directly
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app, db
from app.models import Customer


def backup_db(db_path: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    dest = f"{db_path}.{ts}.bak"
    shutil.copy2(db_path, dest)
    return dest


def normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    # remove common separators
    s = re.sub(r"[\s\-()]+", "", s)
    # keep leading + if present
    has_plus = s.startswith("+")
    s_digits = re.sub(r"[^0-9]", "", s)

    if not s_digits:
        return None

    # If starts with '0' (local format), replace leading 0 with country code
    if s_digits.startswith("0"):
        # drop single leading zero
        rest = s_digits[1:]
        return "+63" + rest

    # If starts with '63', assume country code present without plus
    if s_digits.startswith("63"):
        return "+" + s_digits

    # If it's 10 digits and starts with 9 (mobile without leading 0)
    if len(s_digits) == 10 and s_digits.startswith("9"):
        return "+63" + s_digits

    # If it's 11 digits and starts with 7 or 2 etc (landline with leading 0 dropped?),
    # try to treat as local with leading 0 missing
    if len(s_digits) in (7, 8, 9, 11):
        # best-effort: prefix +63 if it seems plausible
        return "+63" + s_digits

    # If it already had a plus and digits, return normalized +digits
    if has_plus:
        return "+" + s_digits

    # Otherwise give up
    return None


def looks_like_ph_mobile(norm: str) -> bool:
    # Accept +63 followed by 10 digits (mobile) or longer plausible numbers
    if not norm:
        return False
    m = re.fullmatch(r"\+63(\d{9,11})$", norm)
    return bool(m)


def main():
    app = create_app()
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance", "laundry.db"))
    if not os.path.exists(db_path):
        print("Database not found at", db_path)
        return

    bak = backup_db(db_path)
    print("Backed up DB to", bak)

    with app.app_context():
        customers = Customer.query.all()
        changed = 0
        samples = []
        for c in customers:
            orig = c.phone or ""
            norm = normalize_phone(orig)
            if norm and norm != orig and looks_like_ph_mobile(norm):
                samples.append((c.id, orig, norm))
                c.phone = norm
                changed += 1
        if changed > 0:
            db.session.commit()
        print(f"Processed {len(customers)} customers, updated {changed} phones")
        if samples:
            print("Sample updates (id, old, new):")
            for s in samples[:25]:
                print(s)


if __name__ == "__main__":
    main()
