from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    # If there are no users yet, guide the operator to create the first
    # account via the signup page which will be promoted to super_admin.
    try:
        user_count = User.query.count()
    except Exception:
        user_count = 0

    if user_count == 0:
        flash("No users found. Please create the first Super Admin account.", category="warning")
        return redirect(url_for("auth.signup"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Please fill in all fields.", category="error")
            return render_template("login.html", user=current_user)

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                # If the user is required to change password, force them to the change page
                if getattr(user, "must_change_password", False):
                    login_user(user, remember=True)
                    flash("You must change your password before continuing.", category="warning")
                    return redirect(url_for("auth.force_change_password"))

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


@auth.route("/force-change-password", methods=["GET", "POST"])
@login_required
def force_change_password():
    # Only allow access if the current user is required to change password
    if not getattr(current_user, "must_change_password", False):
        return redirect(url_for("views.dashboard"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            flash("Please fill in all fields.", category="error")
            return render_template("force_change_password.html", user=current_user)

        if new_password != confirm_password:
            flash("Passwords do not match.", category="error")
            return render_template("force_change_password.html", user=current_user)

        if len(new_password) < 7:
            flash("Password must be at least 7 characters.", category="error")
            return render_template("force_change_password.html", user=current_user)

        # Update the user's password and clear the must_change_password flag
        user = User.query.get(current_user.id)
        user.password = generate_password_hash(new_password, method="pbkdf2:sha256")
        user.must_change_password = False
        db.session.commit()

        flash("Password updated. You may continue.", category="success")
        return redirect(url_for("views.dashboard"))

    return render_template("force_change_password.html", user=current_user)
