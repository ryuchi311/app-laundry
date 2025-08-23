import os
import random
import sys
from datetime import datetime, timedelta
from typing import List, Tuple

# Ensure project root is on sys.path when running as a standalone script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

    # Intentional: scripts adjust sys.path before importing the app
    from app import create_app, db  # type: ignore  # noqa: E402
    from app.models import Customer, Laundry, Service  # type: ignore  # noqa: E402

try:
    # Optional: reuse generator from app.laundry if available
    from app.laundry import generate_laundry_id  # type: ignore
except Exception:

    def generate_laundry_id() -> str:
        return "".join(random.choice("0123456789") for _ in range(10))


STATUSES: List[str] = [
    "Received",
    "In Process",
    "Ready for Pickup",
    "Completed",
    "Picked Up",
]


def get_or_create_default_customer() -> Customer:
    cust = Customer.query.first()
    if cust:
        return cust
    cust = Customer()
    cust.full_name = "Walk-in Customer"
    cust.email = None
    cust.phone = ""
    db.session.add(cust)
    db.session.commit()
    return cust


def ensure_min_services() -> List[Service]:
    services = Service.query.filter_by(is_active=True).all()
    if services:
        return services
    # Create a few basic services if none exist
    defaults: List[Tuple[str, float, float, str, str, int]] = [
        ("Wash & Dry", 200.0, 0.0, "fas fa-tshirt", "Standard", 24),
        ("Wash & Fold", 250.0, 0.0, "fas fa-tshirt", "Standard", 24),
        ("Full Service", 300.0, 0.0, "fas fa-soap", "Premium", 24),
    ]
    created = []
    for name, base, per_kg, icon, category, esth in defaults:
        s = Service()
        s.name = name
        s.base_price = base
        s.price_per_kg = per_kg
        s.icon = icon
        s.category = category
        s.estimated_hours = esth
        s.is_active = True
        db.session.add(s)
        created.append(s)
    db.session.commit()
    return created


def pick_time_tomorrow(index: int, total: int) -> datetime:
    tomorrow = datetime.utcnow().date() + timedelta(days=1)
    start = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 8, 0, 0)
    end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 20, 0, 0)
    span_seconds = int((end - start).total_seconds())
    # Spread roughly across the day
    offset = int(span_seconds * (index + 0.5) / max(total, 1))
    jitter = random.randint(-900, 900)  # +/- 15 minutes
    ts = start + timedelta(seconds=max(0, min(span_seconds, offset + jitter)))
    return ts


def seed_tomorrow(count: int = 20) -> int:
    random.seed()
    services = ensure_min_services()
    customer = get_or_create_default_customer()

    created = 0
    for i in range(count):
        service = random.choice(services)
        item_count = random.randint(1, 8)
        weight_kg = round(random.uniform(1.0, 8.0), 1)
        when = pick_time_tomorrow(i, count)
        status = random.choices(
            STATUSES,
            weights=[25, 25, 20, 20, 10],  # bias toward early/mid statuses
            k=1,
        )[0]

        # Ensure unique laundry_id
        lid = generate_laundry_id()
        while Laundry.query.filter_by(laundry_id=lid).first() is not None:
            lid = generate_laundry_id()

    laundry = Laundry()
    laundry.laundry_id = lid
    laundry.customer_id = customer.id
    laundry.item_count = item_count
    laundry.service_id = service.id
    laundry.service = service
    laundry.service_type = service.name
    laundry.weight_kg = weight_kg
    laundry.date_received = when
    laundry.status = status
    laundry.update_price()

    db.session.add(laundry)
    created += 1

    db.session.commit()
    return created


def main(argv: List[str]) -> None:
    # Parse optional count from args
    n = 20
    for a in argv:
        if a.startswith("--count="):
            try:
                n = max(1, int(a.split("=", 1)[1]))
            except Exception:
                pass
    app = create_app()
    with app.app_context():
        c = seed_tomorrow(n)
        print(f"Seeded {c} laundries for tomorrow.")


if __name__ == "__main__":
    main(sys.argv[1:])
