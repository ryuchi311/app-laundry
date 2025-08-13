import random
import string
import json
import math
from datetime import datetime, timedelta

from app import create_app, db
from app.models import (
    User, Customer, Service, Laundry, LaundryStatusHistory,
    InventoryCategory, InventoryItem, StockMovement,
    ExpenseCategory, Expense, SalesReport,
    LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction,
    Notification, BusinessSettings
)


def rand_phone():
    return "+63" + "9" + "".join(random.choices(string.digits, k=9))


def ensure_employee():
    user = User.query.filter_by(email="employee@seed.local").first()
    if not user:
        user = User()
        user.email = "employee@seed.local"
        user.password = "test1234"  # seed only
        user.full_name = "Seed Employee"
        user.phone = rand_phone()
        user.role = "employee"
        user.is_active = True
        db.session.add(user)
        db.session.commit()
    return user


def ensure_loyalty_program():
    lp = LoyaltyProgram.query.first()
    if not lp:
        lp = LoyaltyProgram()
        db.session.add(lp)
        db.session.commit()
    return lp


def ensure_services():
    presets = [
        ("Wash Only", 150, 0.0, "fas fa-soap", "Standard", 12),
        ("Dry Only", 120, 0.0, "fas fa-wind", "Standard", 6),
        ("Wash & Dry", 200, 0.0, "fas fa-tshirt", "Standard", 18),
        ("Wash & Fold", 250, 0.0, "fas fa-hands", "Premium", 24),
        ("Full Service", 300, 0.0, "fas fa-broom", "Premium", 36),
        ("Express Service", 280, 0.0, "fas fa-bolt", "Express", 6),
        ("Weight-Based Wash", 80, 30.0, "fas fa-weight", "Standard", 24),
    ]
    created = 0
    for name, base, perkg, icon, cat, esth in presets:
        s = Service.query.filter_by(name=name).first()
        if not s:
            s = Service()
            s.name = name
            s.base_price = base
            s.price_per_kg = perkg
            s.icon = icon
            s.category = cat
            s.estimated_hours = esth
            db.session.add(s)
            created += 1
    if created:
        db.session.commit()


def ensure_inventory(employee_id: int):
    cat = InventoryCategory.query.filter_by(name="Laundry Supplies").first()
    if not cat:
        cat = InventoryCategory(name="Laundry Supplies", description="Detergents, softeners, bags, etc.")
        db.session.add(cat)
        db.session.commit()

    items = [
        ("Detergent Powder (kg)", 50, 10, 200, "kg", 120.0, 0.0),
        ("Fabric Softener (L)", 40, 8, 120, "L", 90.0, 0.0),
        ("Plastic Bags", 1000, 200, 5000, "pieces", 0.8, 0.0),
        ("Hangers", 300, 50, 1000, "pieces", 3.0, 0.0),
        ("Garment Tags", 800, 200, 3000, "pieces", 0.5, 0.0),
    ]
    created = []
    for name, cur, min_s, max_s, uom, cost, sp in items:
        item = InventoryItem.query.filter_by(name=name).first()
        if not item:
            item = InventoryItem(
                name=name,
                category_id=cat.id,
                current_stock=cur,
                minimum_stock=min_s,
                maximum_stock=max_s,
                unit_of_measure=uom,
                cost_per_unit=cost,
                selling_price=sp,
                created_by=employee_id,
            )
            db.session.add(item)
            created.append(item)
    if created:
        db.session.commit()

    return InventoryItem.query.filter(InventoryItem.category_id == cat.id).all()


def ensure_expense_categories():
    names = ["Rent", "Electricity", "Water", "Supplies", "Maintenance", "Internet"]
    for n in names:
        if not ExpenseCategory.query.filter_by(name=n).first():
            ec = ExpenseCategory()
            ec.name = n
            db.session.add(ec)
    db.session.commit()


def create_customers(target_count=500):
    existing = Customer.query.count()
    to_create = max(0, target_count - existing)
    if to_create <= 0:
        return Customer.query.all()

    first_names = [
        "Juan", "Maria", "Jose", "Ana", "Mark", "Jen", "Paolo", "Grace", "Leo", "Rhea",
        "Allan", "Cathy", "Dennis", "Ella", "Francis", "Gina", "Henry", "Ivy", "Joel", "Kris",
        "Ramon", "Liza", "Victor", "Nina", "Arman", "Bianca", "Chris", "Donna", "Edgar", "Faye",
        "Jorge", "Lourdes", "Marco", "Nora", "Oscar", "Patty", "Queenie", "Rico", "Sofia", "Tomas",
    ]
    middle_names = [
        "Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Lopez", "Gonzales", "Torres", "Ramos", "Aquino",
        "Navarro", "Mendoza", "Castro", "Perez", "Flores", "De Leon", "Gutierrez", "Domingo", "Valdez", "Padilla",
    ]
    last_names = [
        "Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Lopez", "Gonzales", "Torres", "Ramos", "Aquino",
        "Navarro", "Mendoza", "Castro", "Perez", "Flores", "De Leon", "Gutierrez", "Domingo", "Valdez", "Padilla",
    ]

    # Prevent duplicate names/emails across DB and this batch
    existing_name_rows = db.session.query(Customer.full_name).all()
    existing_email_rows = db.session.query(Customer.email).all()
    used_names = {n for (n,) in existing_name_rows if n}
    used_emails = {e for (e,) in existing_email_rows if e}
    used_firstnames = { (n.split()[0] if n else '') for (n,) in existing_name_rows }

    def make_unique_name_email():
        for _ in range(30):
            fn = random.choice(first_names)
            if random.random() < 0.15:
                fn += f" {random.choice(first_names)}"
            parts = [fn]
            if random.random() < 0.5:
                if random.random() < 0.6:
                    parts.append(random.choice(middle_names)[0] + ".")
                else:
                    parts.append(random.choice(middle_names))
            ln = random.choice(last_names)
            if random.random() < 0.2:
                ln = f"{ln} {random.choice(last_names)}"
            # Enforce unique first name token
            base_first = parts[0].split()[0]
            if base_first in used_firstnames:
                attempts = 0
                while base_first in used_firstnames and attempts < 10:
                    base_first = random.choice(first_names)
                    attempts += 1
                if base_first in used_firstnames:
                    base_first = base_first + str(random.randint(10,99))
            parts[0] = base_first
            full = f"{parts[0]} {' '.join(parts[1:])} {ln}".replace("  ", " ").strip()
            email = f"{fn.split(' ')[0].lower()}.{ln.split(' ')[-1].lower()}.{random.randint(1000,9999)}@example.com"
            if full not in used_names and email not in used_emails and base_first not in used_firstnames:
                used_names.add(full)
                used_emails.add(email)
                used_firstnames.add(base_first)
                return full, email
        # Fallback
        token = random.randint(10000, 99999)
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        # make first token unique via token
        first_unique = fn + str(token % 100)
        full = f"{first_unique} {ln} {token}"
        email = f"{fn.lower()}.{ln.lower()}.{token}@example.com"
        used_names.add(full)
        used_emails.add(email)
        used_firstnames.add(first_unique)
        return full, email

    created = []
    for _ in range(to_create):
        name, email = make_unique_name_email()
        c = Customer()
        c.full_name = name
        c.email = email
        c.phone = rand_phone()
        db.session.add(c)
        created.append(c)
        if len(created) % 200 == 0:
            db.session.commit()
    if created:
        db.session.commit()
    return Customer.query.all()


def gen_laundry_id(seq: int, day: datetime):
    return f"L{day.strftime('%y%m%d')}{seq:03d}"


def get_unique_laundry_id(base_day: datetime, start_seq: int) -> tuple[str, int]:
    """Generate a unique laundry_id for reruns by bumping seq until available."""
    seq = start_seq
    while True:
        lid = gen_laundry_id(seq, base_day)
        exists = Laundry.query.filter_by(laundry_id=lid).first()
        if not exists:
            return lid, seq
        seq += 1


def add_status_history(laundry: Laundry, user_id: int, old_status: str | None, new_status: str, when: datetime):
    hist = LaundryStatusHistory.log_status_change(
        laundry_id=laundry.laundry_id,
        old_status=old_status,
        new_status=new_status,
        changed_by=user_id,
        notes=None,
    )
    if hist:
        hist.changed_at = when
        db.session.add(hist)


def consume_inventory_for_order(items, laundry: Laundry, user_id: int):
    weight = laundry.weight_kg or max(2.0, laundry.item_count * 0.6)
    consumption_plan = {
        "Detergent Powder (kg)": max(1, math.ceil(weight * 0.12)),
        "Fabric Softener (L)": max(1, math.ceil(weight * 0.05)),
        "Plastic Bags": max(1, laundry.item_count // 2 + 1),
        "Hangers": max(0, (laundry.item_count // 2) if "Iron" in laundry.get_service_name() else 0),
        "Garment Tags": 1,
    }
    items_by_name = {i.name: i for i in items}
    for name, qty in consumption_plan.items():
        item = items_by_name.get(name)
        if not item or qty <= 0:
            continue
        StockMovement.create_movement(
            item_id=item.id,
            movement_type="USAGE",
            quantity=int(qty),
            created_by=user_id,
            reference_type="LAUNDRY",
            reference_id=laundry.laundry_id,
            notes=f"Consumption for {laundry.laundry_id} ({laundry.get_service_name()})",
            unit_cost=item.cost_per_unit,
        )


def maybe_restock_inventory(items, user_id: int, day: datetime):
    if day.weekday() != 0:
        return
    for item in items:
        if item.current_stock <= item.minimum_stock * 1.5:
            qty = max(item.maximum_stock - item.current_stock, int(item.minimum_stock * 1.5))
            StockMovement.create_movement(
                item_id=item.id,
                movement_type="PURCHASE",
                quantity=int(qty),
                created_by=user_id,
                reference_type="PURCHASE",
                reference_id=f"PO-{day.strftime('%Y%m%d')}",
                notes=f"Weekly restock on {day.date().isoformat()}",
                unit_cost=item.cost_per_unit,
            )


def add_expenses_for_day(user_id: int, day: datetime):
    def add_exp(title, amount, category_name):
        cat = ExpenseCategory.query.filter_by(name=category_name).first()
        e = Expense()
        e.title = title
        e.description = title
        e.amount = amount
        e.category_id = cat.id if cat else None
        e.expense_date = day.date()
        e.payment_method = "CASH"
        e.payment_status = "PAID"
        e.created_by = user_id
        e.generate_expense_id()
        db.session.add(e)

    if day.day == 1:
        add_exp("Shop Rent", 15000.0, "Rent")
        add_exp("Internet Bill", 1500.0, "Internet")

    if day.weekday() == 4:
        add_exp("Electricity Bill (weekly est)", 3800.0, "Electricity")
        add_exp("Water Bill (weekly est)", 900.0, "Water")

    if day.day == 15:
        add_exp("Machine Maintenance", 2500.0, "Maintenance")


def finalize_loyalty_for_order(lp: LoyaltyProgram, customer: Customer, laundry: Laundry, user_id: int):
    loyalty = customer.get_loyalty_info()
    loyalty.total_orders += 1
    loyalty.total_spent += laundry.price
    loyalty.last_order_date = laundry.date_updated

    tier, multiplier, _, _ = lp.get_tier_info(loyalty.total_points_earned)
    earned = int(max(0, laundry.price) * lp.points_per_peso * multiplier)
    loyalty.total_points_earned += earned
    loyalty.current_points += earned
    loyalty.update_tier(lp)

    lt = LoyaltyTransaction()
    lt.customer_loyalty_id = loyalty.id
    lt.transaction_type = "EARNED"
    lt.points = earned
    lt.description = f"Points from {laundry.laundry_id}"
    lt.laundry_id = laundry.id
    lt.order_amount = laundry.price
    lt.created_by = user_id
    db.session.add(lt)


def daily_sales_report(day: datetime, user_id: int):
    day_start = datetime(day.year, day.month, day.day)
    day_end = day_start + timedelta(days=1)
    laundries = Laundry.query.filter(Laundry.date_received >= day_start, Laundry.date_received < day_end).all()

    total_laundries = len(laundries)
    total_revenue = sum(l.price for l in laundries if l.status == "Completed")

    expenses = Expense.query.filter(Expense.expense_date == day.date()).all()
    total_expenses = sum(e.amount for e in expenses)

    breakdown = {}
    for l in laundries:
        name = l.get_service_name()
        breakdown.setdefault(name, {"count": 0, "revenue": 0.0})
        breakdown[name]["count"] += 1
        if l.status == "Completed":
            breakdown[name]["revenue"] += l.price

    sr = SalesReport()
    sr.report_date = day.date()
    sr.report_type = "DAILY"
    sr.total_laundries = total_laundries
    sr.total_revenue = total_revenue
    sr.total_expenses = total_expenses
    sr.net_profit = total_revenue - total_expenses
    sr.service_breakdown = json.dumps(breakdown)
    sr.generated_by = user_id
    db.session.add(sr)


def seed_two_months():
    app = create_app()
    with app.app_context():
        random.seed(42)

        employee = ensure_employee()
        lp = ensure_loyalty_program()
        ensure_services()
        ensure_expense_categories()
        items = ensure_inventory(employee.id)
        customers = create_customers(500)

        services = Service.query.filter_by(is_active=True).all()
        if not services:
            raise RuntimeError("No services available to seed orders.")

        end_day = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        start_day = end_day - timedelta(days=60)

        seq_counter = 1
        total_orders = 0

        day = start_day
        while day <= end_day:
            daily_orders = random.randint(25, 60)
            if random.random() < 0.08:
                daily_orders = random.randint(8, 16)

            for _ in range(daily_orders):
                customer = random.choice(customers)
                service = random.choice(services)

                item_count = random.randint(3, 18)
                weight_kg = round(random.uniform(2.0, 12.0), 1)

                laundry = Laundry()
                unique_id, seq_counter = get_unique_laundry_id(day, seq_counter)
                laundry.laundry_id = unique_id
                laundry.customer_id = customer.id
                laundry.service_id = service.id
                laundry.item_count = item_count
                laundry.weight_kg = weight_kg
                laundry.status = "Received"
                laundry.notes = None
                laundry.date_received = day + timedelta(hours=random.randint(8, 19), minutes=random.randint(0, 59))
                laundry.last_edited_by = employee.id
                laundry.last_edited_at = day
                laundry.edit_count = 1
                laundry.is_modified = False
                laundry.update_price()
                db.session.add(laundry)

                t0 = laundry.date_received
                add_status_history(laundry, employee.id, None, "Received", t0)

                t1 = t0 + timedelta(hours=random.uniform(0.5, 2.5))
                laundry.status = "In Process"
                laundry.date_updated = t1
                add_status_history(laundry, employee.id, "Received", "In Process", t1)

                db.session.flush()
                consume_inventory_for_order(items, laundry, employee.id)

                if random.random() < 0.7:
                    t2 = t1 + timedelta(hours=random.uniform(2.0, 10.0))
                else:
                    t2 = t1 + timedelta(hours=random.uniform(14.0, 30.0))

                laundry.status = "Ready for Pickup"
                laundry.date_updated = t2
                add_status_history(laundry, employee.id, "In Process", "Ready for Pickup", t2)

                final = "Completed"
                t3 = t2 + timedelta(hours=random.uniform(1.0, 8.0))
                laundry.status = final
                laundry.date_updated = t3
                add_status_history(laundry, employee.id, "Ready for Pickup", final, t3)

                finalize_loyalty_for_order(lp, customer, laundry, employee.id)

                if random.random() < 0.15:
                    db.session.add(Notification(
                        user_id=employee.id,
                        title=f"Order {laundry.laundry_id} {final}",
                        message=f"{customer.full_name}'s order is {final}.",
                        notification_type="info",
                        related_model="laundry",
                        related_id=laundry.laundry_id,
                        action_url=f"/laundry?laundry_id={laundry.laundry_id}",
                        action_text="View",
                    ))

                seq_counter += 1
                total_orders += 1

                if total_orders % 200 == 0:
                    db.session.commit()

            maybe_restock_inventory(items, employee.id, day)
            add_expenses_for_day(employee.id, day)
            daily_sales_report(day, employee.id)
            db.session.commit()

            day += timedelta(days=1)

        BusinessSettings.get_settings()

        print("Seeding complete ✅")
        print(f"Customers: {Customer.query.count()}")
        print(f"Services:  {Service.query.count()}")
        print(f"Laundries: {Laundry.query.count()}")
        print(f"Expenses:  {Expense.query.count()}")
        print(f"Inventory Items: {InventoryItem.query.count()}")
        print(f"Stock Movements: {StockMovement.query.count()}")
        print(f"Loyalty Tx: {LoyaltyTransaction.query.count()}")
        print(f"Sales Reports: {SalesReport.query.count()}")


if __name__ == "__main__":
    seed_two_months()
