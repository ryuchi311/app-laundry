import os
import random
import string
import sys
from collections import defaultdict

# Ensure project root is on sys.path for standalone execution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

    # Intentional: scripts adjust sys.path before importing the app
    from app import create_app, db  # noqa: E402
    from app.models import Customer  # noqa: E402


def uniq_token() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=2))


def dedupe_firstnames(dry_run: bool = False) -> dict:
    stats = {"groups": 0, "fixed": 0}
    app = create_app()
    with app.app_context():
        rows = Customer.query.order_by(Customer.id.asc()).all()
        groups = defaultdict(list)
        for c in rows:
            if c.full_name:
                first = c.full_name.strip().split()[0]
                groups[first].append(c)
        for first, entries in groups.items():
            if len(entries) <= 1:
                continue
            stats["groups"] += 1
            # Keep first entry unchanged; alter the rest's first token to make it unique
            for idx, c in enumerate(entries[1:], start=1):
                parts = c.full_name.strip().split()
                if not parts:
                    continue
                new_first = parts[0] + uniq_token()
                parts[0] = new_first
                new_name = " ".join(parts)
                if not dry_run:
                    c.full_name = new_name
                stats["fixed"] += 1
        if not dry_run:
            db.session.commit()
    return stats


if __name__ == "__main__":
    res = dedupe_firstnames(dry_run=False)
    print(f"Duplicate first-name groups: {res['groups']}")
    print(f"Customers updated:           {res['fixed']}")
