import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from . import db
from .decorators import super_admin_required
from .models import User

user_management = Blueprint("user_management", __name__)


@user_management.route("/users")
@super_admin_required
def list_users():
    """List all users (Super Admin only)"""
    users = User.query.order_by(User.date_created.desc()).all()
    return render_template("user_management/list_users.html", users=users)


@user_management.route("/users/add", methods=["GET", "POST"])
@super_admin_required
def add_user():
    """Add new user (Super Admin only)"""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "user")
        password = request.form.get("password", "").strip()

        # Validation
        errors = []

        if not full_name:
            errors.append("Full name is required")

        if not email:
            errors.append("Email is required")
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            errors.append("Please enter a valid email address")
        elif User.query.filter_by(email=email).first():
            errors.append("Email address is already in use")

        if not password:
            errors.append("Password is required")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters long")

        if role not in ["user", "admin", "super_admin"]:
            errors.append("Invalid role selected")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            try:
                new_user = User()
                new_user.full_name = full_name
                new_user.email = email
                new_user.phone = phone
                new_user.role = role
                # Use a supported scheme; 'sha256' can raise in newer Werkzeug versions
                new_user.password = generate_password_hash(
                    password, method="pbkdf2:sha256"
                )

                db.session.add(new_user)
                db.session.commit()
                flash(f"User {full_name} has been created successfully!", "success")
                return redirect(url_for("user_management.list_users"))
            except Exception:
                db.session.rollback()
                flash(
                    "An error occurred while creating the user. Please try again.",
                    "error",
                )

    return render_template("user_management/add_user.html")


@user_management.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@super_admin_required
def edit_user(user_id):
    """Edit user (Super Admin only)"""
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        role = request.form.get("role", "user")
        is_active = request.form.get("is_active") == "on"

        # Validation
        errors = []

        if not full_name:
            errors.append("Full name is required")

        if not email:
            errors.append("Email is required")
        elif not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            errors.append("Please enter a valid email address")
        elif email != user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append("Email address is already in use")

        if role not in ["user", "admin", "super_admin"]:
            errors.append("Invalid role selected")

        # Prevent removing super admin role from the last super admin
        if user.role == "super_admin" and role != "super_admin":
            super_admin_count = User.query.filter_by(role="super_admin").count()
            if super_admin_count <= 1:
                errors.append(
                    "Cannot remove super admin role from the last super administrator"
                )

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            try:
                user.full_name = full_name
                user.email = email
                user.phone = phone
                user.role = role
                user.is_active = is_active

                db.session.commit()
                flash(f"User {full_name} has been updated successfully!", "success")
                return redirect(url_for("user_management.list_users"))
            except Exception:
                db.session.rollback()
                flash(
                    "An error occurred while updating the user. Please try again.",
                    "error",
                )

    return render_template("user_management/edit_user.html", user=user)


@user_management.route("/users/<int:user_id>/delete", methods=["POST"])
@super_admin_required
def delete_user(user_id):
    """Delete user (Super Admin only)"""
    user = User.query.get_or_404(user_id)

    # Prevent deleting the current user
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "error")
        return redirect(url_for("user_management.list_users"))

    # Prevent deleting the last super admin
    if user.role == "super_admin":
        super_admin_count = User.query.filter_by(role="super_admin").count()
        if super_admin_count <= 1:
            flash("Cannot delete the last super administrator.", "error")
            return redirect(url_for("user_management.list_users"))

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"User {user.full_name} has been deleted successfully!", "success")
    except Exception:
        db.session.rollback()
        flash("An error occurred while deleting the user. Please try again.", "error")

    return redirect(url_for("user_management.list_users"))


@user_management.route("/users/<int:user_id>/reset_password", methods=["POST"])
@super_admin_required
def reset_password(user_id):
    """Reset user password (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get("new_password", "").strip()

    if not new_password:
        flash("New password is required", "error")
    elif len(new_password) < 6:
        flash("Password must be at least 6 characters long", "error")
    else:
        try:
            # Use a supported scheme; 'sha256' can raise in newer Werkzeug versions
            user.password = generate_password_hash(new_password, method="pbkdf2:sha256")
            db.session.commit()
            flash(f"Password reset successfully for {user.full_name}!", "success")
        except Exception as e:
            db.session.rollback()
            # Surface a concise diagnostic in logs; keep UX generic
            print(f"Password reset error for user {user_id}: {e}")
            flash(
                "An error occurred while resetting the password. Please try again.",
                "error",
            )

    return redirect(url_for("user_management.edit_user", user_id=user_id))
