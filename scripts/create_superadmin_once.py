#!/usr/bin/env python3
"""Create a single superadmin user from environment variables and exit.

This script is intended to be run once (manually or in a deployment hook) to
create a secure Super Admin account without exposing the public signup form.

Environment variables used:
 - SUPERADMIN_EMAIL
 - SUPERADMIN_PASSWORD
 - SUPERADMIN_FULLNAME (optional)

Usage:
  python3 scripts/create_superadmin_once.py

"""
import os
import sys

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash


def main():
    email = os.environ.get("SUPERADMIN_EMAIL")
    password = os.environ.get("SUPERADMIN_PASSWORD")
    fullname = os.environ.get("SUPERADMIN_FULLNAME", "Super Administrator")

    if not email or not password:
        print("Please set SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD environment variables.")
        sys.exit(2)

    app = create_app()
    with app.app_context():
        # Ensure tables exist
        db.create_all()

        if User.query.count() > 0:
            print("Users already exist. Aborting to avoid overwriting roles.")
            sys.exit(1)

        u = User()
        u.email = email
        u.full_name = fullname
        u.role = "super_admin"
        u.password = generate_password_hash(password, method="pbkdf2:sha256")
        u.is_active = True
        u.must_change_password = True
        db.session.add(u)
        db.session.commit()
        print(f"Created super admin: {email}")


if __name__ == "__main__":
    main()
