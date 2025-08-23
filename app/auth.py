from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Please fill in all fields.", category="error")
            return render_template("login.html", user=current_user)

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in successfully!", category="success")
                login_user(user, remember=True)
                return redirect(url_for("views.dashboard"))
            else:
                flash("Incorrect password, try again.", category="error")
        else:
            flash("Email does not exist.", category="error")

    return render_template("login.html", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email")
        full_name = request.form.get("fullName")
        phone = request.form.get("phone")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # Check for None values first
        if not email or not full_name or not password1 or not password2:
            flash("Please fill in all required fields.", category="error")
            return render_template("signup.html", user=current_user)

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already exists.", category="error")
        elif len(email) < 4:
            flash("Email must be greater than 3 characters.", category="error")
        elif len(full_name) < 2:
            flash("Full name must be greater than 1 character.", category="error")
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
        elif len(password1) < 7:
            flash("Password must be at least 7 characters.", category="error")
        else:
            # Check if this is the first user (make them super admin)
            user_count = User.query.count()
            is_first_user = user_count == 0

            # Create new user with proper attribute assignment
            new_user = User()
            new_user.email = email
            new_user.full_name = full_name
            new_user.phone = phone
            new_user.password = generate_password_hash(
                password1, method="pbkdf2:sha256"
            )
            new_user.role = "super_admin" if is_first_user else "user"
            new_user.is_active = True

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)

            if is_first_user:
                flash(
                    "Account created! You are now the Super Administrator.",
                    category="success",
                )
            else:
                flash("Account created!", category="success")
            return redirect(url_for("views.dashboard"))

    return render_template("signup.html", user=current_user)
