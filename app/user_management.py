from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from .models import User
from .decorators import super_admin_required, admin_required
from . import db
import re

user_management = Blueprint('user_management', __name__)

@user_management.route('/users')
@super_admin_required
def list_users():
    """List all users (Super Admin only)"""
    users = User.query.order_by(User.date_created.desc()).all()
    pending_users_count = User.query.filter_by(is_approved=None).filter(User.role != 'super_admin').count()
    return render_template('user_management/list_users.html', users=users, pending_users_count=pending_users_count)

@user_management.route('/users/add', methods=['GET', 'POST'])
@super_admin_required
def add_user():
    """Add new user (Super Admin only)"""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'user')
        password = request.form.get('password', '').strip()
        
        # Validation
        errors = []
        
        if not full_name:
            errors.append('Full name is required')
        
        if not email:
            errors.append('Email is required')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address')
        elif User.query.filter_by(email=email).first():
            errors.append('Email address is already in use')
        
        if not password:
            errors.append('Password is required')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        if role not in ['user', 'admin', 'super_admin']:
            errors.append('Invalid role selected')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            try:
                new_user = User()
                new_user.full_name = full_name
                new_user.email = email
                new_user.phone = phone
                new_user.role = role
                new_user.password = generate_password_hash(password, method='sha256')
                new_user.is_approved = True  # Admin-created users are auto-approved
                
                db.session.add(new_user)
                db.session.commit()
                flash(f'User {full_name} has been created successfully!', 'success')
                return redirect(url_for('user_management.list_users'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while creating the user. Please try again.', 'error')
    
    return render_template('user_management/add_user.html')

@user_management.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@super_admin_required
def edit_user(user_id):
    """Edit user (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'user')
        is_active = request.form.get('is_active') == 'on'
        
        # Validation
        errors = []
        
        if not full_name:
            errors.append('Full name is required')
        
        if not email:
            errors.append('Email is required')
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Please enter a valid email address')
        elif email != user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('Email address is already in use')
        
        if role not in ['user', 'admin', 'super_admin']:
            errors.append('Invalid role selected')
        
        # Prevent removing super admin role from the last super admin
        if user.role == 'super_admin' and role != 'super_admin':
            super_admin_count = User.query.filter_by(role='super_admin').count()
            if super_admin_count <= 1:
                errors.append('Cannot remove super admin role from the last super administrator')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            try:
                user.full_name = full_name
                user.email = email
                user.phone = phone
                user.role = role
                user.is_active = is_active
                
                db.session.commit()
                flash(f'User {full_name} has been updated successfully!', 'success')
                return redirect(url_for('user_management.list_users'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating the user. Please try again.', 'error')
    
    return render_template('user_management/edit_user.html', user=user)

@user_management.route('/users/<int:user_id>/delete', methods=['POST'])
@super_admin_required
def delete_user(user_id):
    """Delete user (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the current user
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('user_management.list_users'))
    
    # Prevent deleting the last super admin
    if user.role == 'super_admin':
        super_admin_count = User.query.filter_by(role='super_admin').count()
        if super_admin_count <= 1:
            flash('Cannot delete the last super administrator.', 'error')
            return redirect(url_for('user_management.list_users'))
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'User {user.full_name} has been deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the user. Please try again.', 'error')
    
    return redirect(url_for('user_management.list_users'))

@user_management.route('/users/<int:user_id>/reset_password', methods=['POST'])
@super_admin_required
def reset_password(user_id):
    """Reset user password (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password:
        flash('New password is required', 'error')
    elif len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
    else:
        try:
            user.password = generate_password_hash(new_password, method='sha256')
            db.session.commit()
            flash(f'Password reset successfully for {user.full_name}!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while resetting the password. Please try again.', 'error')
    
    return redirect(url_for('user_management.edit_user', user_id=user_id))

@user_management.route('/users/pending')
@super_admin_required
def pending_users():
    """List users pending approval (Super Admin only)"""
    users = User.query.filter_by(is_approved=None).filter(User.role != 'super_admin').order_by(User.date_created.desc()).all()
    return render_template('user_management/pending_users.html', users=users)

@user_management.route('/users/<int:user_id>/approve', methods=['POST'])
@super_admin_required
def approve_user(user_id):
    """Approve a pending user (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    
    if user.role == 'super_admin':
        flash('Cannot approve super admin users.', 'error')
        return redirect(url_for('user_management.pending_users'))
    
    if user.is_approved:
        flash('User is already approved.', 'info')
        return redirect(url_for('user_management.pending_users'))
    
    try:
        user.approve_user(current_user.id)
        db.session.commit()
        flash(f'User {user.full_name} has been approved successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while approving the user. Please try again.', 'error')
    
    return redirect(url_for('user_management.pending_users'))

@user_management.route('/users/<int:user_id>/reject', methods=['POST'])
@super_admin_required  
def reject_user(user_id):
    """Reject a pending user (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    
    if user.role == 'super_admin':
        flash('Cannot reject super admin users.', 'error')
        return redirect(url_for('user_management.pending_users'))
    
    if user.is_approved:
        flash('Cannot reject an already approved user.', 'error')
        return redirect(url_for('user_management.pending_users'))
    
    try:
        user.reject_user()
        db.session.commit()
        flash(f'User {user.full_name} has been rejected and deactivated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while rejecting the user. Please try again.', 'error')
    
    return redirect(url_for('user_management.pending_users'))

@user_management.route('/users/<int:user_id>/activate', methods=['POST'])
@super_admin_required
def activate_user(user_id):
    """Activate a user (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('user_management.list_users'))
    
    if user.is_active:
        flash(f'User {user.full_name or user.email} is already active.', 'info')
        return redirect(url_for('user_management.list_users'))
    
    try:
        user.is_active = True
        db.session.commit()
        flash(f'User {user.full_name or user.email} has been activated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while activating the user. Please try again.', 'error')
    
    return redirect(url_for('user_management.list_users'))

@user_management.route('/users/<int:user_id>/deactivate', methods=['POST'])
@super_admin_required
def deactivate_user(user_id):
    """Deactivate a user (Super Admin only)"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('user_management.list_users'))
    
    if user.role == 'super_admin' and User.query.filter_by(role='super_admin', is_active=True).count() <= 1:
        flash('Cannot deactivate the last active Super Admin.', 'error')
        return redirect(url_for('user_management.list_users'))
    
    if not user.is_active:
        flash(f'User {user.full_name or user.email} is already inactive.', 'info')
        return redirect(url_for('user_management.list_users'))
    
    try:
        user.is_active = False
        db.session.commit()
        flash(f'User {user.full_name or user.email} has been deactivated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deactivating the user. Please try again.', 'error')
    
    return redirect(url_for('user_management.list_users'))
