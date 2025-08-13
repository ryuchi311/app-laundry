import os
import sys
from typing import Optional

# Ensure project root is on sys.path when running as a standalone script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models import Laundry, Service


def summarize() -> None:
    total = Laundry.query.count()
    zero_price = Laundry.query.filter((Laundry.price == 0) | (Laundry.price.is_(None))).count()
    total_completed = Laundry.query.filter_by(status="Completed").count()
    revenue_all = db.session.query(db.func.sum(Laundry.price)).scalar() or 0
    revenue_completed = (
        db.session.query(db.func.sum(Laundry.price))
        .filter(Laundry.status == "Completed")
        .scalar()
        or 0
    )

    services_total = Service.query.count()
    services_zero = Service.query.filter((Service.base_price == 0) | (Service.base_price.is_(None))).count()

    print("=== Laundry Pricing Audit ===")
    print(f"Total laundries: {total}")
    print(f"Price blank/zero: {zero_price}")
    print(f"Total completed: {total_completed}")
    print(f"Revenue (all): {revenue_all:.2f}")
    print(f"Revenue (completed): {revenue_completed:.2f}")
    print()
    print("=== Service Pricing Audit ===")
    print(f"Total services: {services_total}")
    print(f"Services with base_price 0/NULL: {services_zero}")

    # Sample a few problematic laundries
    if zero_price:
        print()
        print("Examples with 0/NULL price:")
        rows = (
            Laundry.query.filter((Laundry.price == 0) | (Laundry.price.is_(None)))
            .order_by(Laundry.date_received.desc())
            .limit(10)
            .all()
        )
        for l in rows:
            print(
                f"- laundry_id={l.laundry_id} service_id={l.service_id} service_type='{l.service_type}' "
                f"item_count={l.item_count} weight_kg={l.weight_kg} status={l.status}"
            )


def backfill_prices(dry_run: bool = False) -> int:
    updated = 0
    rows = Laundry.query.filter((Laundry.price == 0) | (Laundry.price.is_(None))).all()
    for l in rows:
        old = l.price
        l.update_price()
        if (l.price or 0) > 0:
            updated += 1
    if dry_run:
        db.session.rollback()
    else:
        db.session.commit()
    return updated


def main(argv: list[str]) -> None:
    app = create_app()
    with app.app_context():
        if "--fix" in argv or "--backfill" in argv:
            dry = "--dry-run" in argv
            print("Backfilling prices for laundries with 0/NULL price...")
            count = backfill_prices(dry_run=dry)
            if dry:
                print(f"Would update {count} rows (dry-run).")
            else:
                print(f"Updated {count} rows.")
        summarize()


if __name__ == "__main__":
    main(sys.argv[1:])
