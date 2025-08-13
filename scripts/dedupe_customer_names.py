from collections import defaultdict
import os
import sys
import random
import string

# Ensure project root is on sys.path for standalone execution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import Customer


def random_token(n: int = 3) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


def dedupe_names(dry_run: bool = False) -> dict:
    stats = {"duplicates": 0, "updated": 0}
    app = create_app()
    with app.app_context():
        rows = Customer.query.order_by(Customer.id.asc()).all()
        seen = defaultdict(list)
        for c in rows:
            if c.full_name:
                seen[c.full_name].append(c)
        for name, entries in seen.items():
            if len(entries) <= 1:
                continue
            stats["duplicates"] += len(entries) - 1
            # keep the first, adjust the rest
            for idx, c in enumerate(entries[1:], start=1):
                new_name = f"{c.full_name} {random_token()}"
                if not dry_run:
                    c.full_name = new_name
                stats["updated"] += 1
        if not dry_run:
            db.session.commit()
    return stats


if __name__ == "__main__":
    res = dedupe_names(dry_run=False)
    print(f"Duplicates found: {res['duplicates']}")
    print(f"Names updated:   {res['updated']}")
