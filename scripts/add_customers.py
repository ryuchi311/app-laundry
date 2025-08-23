import argparse
import os
import random
import string
import sys
import time

# Ensure project root is on sys.path for standalone execution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

    # Intentional: scripts adjust sys.path before importing the app
    from app import create_app, db  # noqa: E402
    from app.models import Customer  # noqa: E402

FIRST_NAMES = [
    "Juan",
    "Maria",
    "Jose",
    "Ana",
    "Mark",
    "Jen",
    "Paolo",
    "Grace",
    "Leo",
    "Rhea",
    "Allan",
    "Cathy",
    "Dennis",
    "Ella",
    "Francis",
    "Gina",
    "Henry",
    "Ivy",
    "Joel",
    "Kris",
    "Ramon",
    "Liza",
    "Victor",
    "Nina",
    "Arman",
    "Bianca",
    "Chris",
    "Donna",
    "Edgar",
    "Faye",
    "Jorge",
    "Lourdes",
    "Marco",
    "Nora",
    "Oscar",
    "Patty",
    "Queenie",
    "Rico",
    "Sofia",
    "Tomas",
    "Ulysses",
    "Vera",
    "Warren",
    "Xandra",
    "Yuri",
    "Zara",
]

MIDDLE_NAMES = [
    "Santos",
    "Reyes",
    "Cruz",
    "Bautista",
    "Garcia",
    "Lopez",
    "Gonzales",
    "Torres",
    "Ramos",
    "Aquino",
    "Navarro",
    "Mendoza",
    "Castro",
    "Perez",
    "Flores",
    "De Leon",
    "Gutierrez",
    "Domingo",
    "Valdez",
    "Padilla",
    "Ruiz",
    "Salazar",
    "Vergara",
    "Villanueva",
    "Dela Cruz",
    "Del Rosario",
    "Rosales",
    "Sarmiento",
]

LAST_NAMES = [
    "Santos",
    "Reyes",
    "Cruz",
    "Bautista",
    "Garcia",
    "Lopez",
    "Gonzales",
    "Torres",
    "Ramos",
    "Aquino",
    "Navarro",
    "Mendoza",
    "Castro",
    "Perez",
    "Flores",
    "De Leon",
    "Gutierrez",
    "Domingo",
    "Valdez",
    "Padilla",
    "Alvarez",
    "Bernardo",
    "Clemente",
    "Esparza",
    "Ferrer",
    "Herrera",
    "Ibanez",
    "Jimenez",
    "Laguna",
    "Manalo",
    "Natividad",
    "Ocampo",
    "Panganiban",
    "Querubin",
    "Rivera",
    "Solis",
    "Trias",
    "Umali",
    "Velasco",
    "Yabut",
]


def rand_phone() -> str:
    return "+63" + "9" + "".join(random.choices(string.digits, k=9))


def _slugify(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "." for ch in s).strip(".")


def _first_token(name: str) -> str:
    return name.strip().split()[0] if name.strip() else ""


def gen_name_email(
    existing_emails: set[str],
    existing_names: set[str],
    batch_emails: set[str],
    batch_names: set[str],
    used_firstnames: set[str],
) -> tuple[str, str]:
    # Try multiple times to avoid duplicates
    for _ in range(30):
        fn = random.choice(FIRST_NAMES)
        # Optional second first name for variety
        if random.random() < 0.15:
            fn += f" {random.choice(FIRST_NAMES)}"

        # Sometimes include middle initial or middle name
        name_parts = [fn]
        if random.random() < 0.5:
            if random.random() < 0.6:
                name_parts.append(random.choice(MIDDLE_NAMES)[0] + ".")
            else:
                name_parts.append(random.choice(MIDDLE_NAMES))

        # One or two last names
        ln1 = random.choice(LAST_NAMES)
        if random.random() < 0.2:
            ln2 = random.choice(LAST_NAMES)
            ln = f"{ln1} {ln2}"
        else:
            ln = ln1

        # Ensure first-name token uniqueness across DB and batch
        base_first = _first_token(name_parts[0])
        if base_first in used_firstnames:
            # pick another base; try a few attempts
            attempts = 0
            while base_first in used_firstnames and attempts < 10:
                base_first = random.choice(FIRST_NAMES)
                attempts += 1
            if base_first in used_firstnames:
                # synthesize a unique first name
                base_first = base_first + "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=2)
                )
        name_parts[0] = base_first

        full_name = f"{name_parts[0]} {' '.join(name_parts[1:])} {ln}".replace(
            "  ", " "
        ).strip()

        # Craft unique email using slug + random token
        base = _slugify(full_name).replace("..", ".")
        token = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        email = f"{base}.{token}@example.com"

    if (
        full_name not in existing_names
        and full_name not in batch_names
        and email not in existing_emails
        and email not in batch_emails
        and _first_token(full_name) not in used_firstnames
    ):
        used_firstnames.add(_first_token(full_name))
        return full_name, email

    # Fallback with timestamp token to guarantee uniqueness
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    full_name = f"{fn} {ln} {int(time.time())%100000}"
    email = f"{_slugify(full_name)}@example.com"
    return full_name, email


def add_customers(count: int, commit_every: int = 100) -> int:
    # Load existing to avoid duplicates across DB
    existing_email_rows = db.session.query(Customer.email).all()
    existing_name_rows = db.session.query(Customer.full_name).all()
    existing_emails = {e for (e,) in existing_email_rows if e}
    existing_names = {n for (n,) in existing_name_rows if n}
    existing_firstnames = {_first_token(n) for n in existing_names}

    batch_emails: set[str] = set()
    batch_names: set[str] = set()
    batch_firstnames: set[str] = set()

    created = 0
    for _ in range(count):
        name, email = gen_name_email(
            existing_emails,
            existing_names,
            batch_emails,
            batch_names,
            existing_firstnames | batch_firstnames,
        )
        c = Customer()
        c.full_name = name
        c.email = email
        c.phone = rand_phone()
        db.session.add(c)
        created += 1
        batch_emails.add(email)
        batch_names.add(name)
        batch_firstnames.add(_first_token(name))
        if created % commit_every == 0:
            db.session.commit()
    db.session.commit()
    return created


def main():
    parser = argparse.ArgumentParser(description="Add N customers to the database")
    parser.add_argument(
        "--count",
        type=int,
        default=200,
        help="How many customers to create (default: 200)",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        before = Customer.query.count()
        created = add_customers(args.count)
        after = Customer.query.count()
        print(f"Created {created} customers ✅")
        print(f"Customers before: {before}")
        print(f"Customers after:  {after}")


if __name__ == "__main__":
    # Use system randomness for better variety; no explicit seeding
    main()
