#!/usr/bin/env python3
"""Safer normalization: only convert clear Philippine mobile formats.

Rules:
- 11-digit numbers starting with 09 -> +63 9XXXXXXXXX
- 10-digit numbers starting with 9 -> +63 9XXXXXXXXX
- numbers already starting with +63 or 63 are normalized to +63XXXXXXXXXX

Do not touch numbers with other country codes (+1, +44, etc.) or numbers with extensions.
This script will print changes and commit them.
"""
import os
import re
import sys
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app, db
from app.models import Customer


def normalize_safe(raw: str) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    # skip if contains extension characters
    if re.search(r"[xX]|ext|extension", s):
        return None
    # remove separators
    digits = re.sub(r"[^0-9]", "", s)
    if not digits:
        return None

    # already international PH
    if digits.startswith("63") and len(digits) >= 11:
        return "+" + digits

    # local mobile with leading 0 (09XXXXXXXXX -> +639XXXXXXXXX)
    if digits.startswith("09") and len(digits) == 11:
        return "+63" + digits[1:]

    # 10-digit mobile starting with 9 -> +63XXXXXXXXXX
    if len(digits) == 10 and digits.startswith("9"):
        return "+63" + digits

    return None


def main():
    app = create_app()
    with app.app_context():
        customers = Customer.query.all()
        changed = []
        for c in customers:
            orig = c.phone or ""
            new = normalize_safe(orig)
            if new and new != orig:
                changed.append((c.id, orig, new))
                c.phone = new
        if changed:
            db.session.commit()
        print(f"Processed {len(customers)} customers, updated {len(changed)} phones")
        for row in changed[:50]:
            print(row)


if __name__ == "__main__":
    main()
