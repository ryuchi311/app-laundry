from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from . import db
import re

profile = Blueprint('profile', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    # Remove spaces, dashes, and parentheses
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's a valid phone format (10-15 digits)
    pattern = r'^[\+]?[0-9]{10,15}$'
    return re.match(pattern, clean_phone) is not None

@profile.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Get form data
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Validation
            errors = []
            
            if not full_name:
                errors.append('Full name is required')
            elif len(full_name) < 2:
                errors.append('Full name must be at least 2 characters long')
                
            if not email:
                errors.append('Email is required')
            elif not validate_email(email):
                errors.append('Please enter a valid email address')
            elif email != current_user.email:
                # Check if email is already taken
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    errors.append('Email address is already in use')
                    
            if phone and not validate_phone(phone):
                errors.append('Please enter a valid phone number')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
            else:
                try:
                    # Update user profile
                    current_user.full_name = full_name
                    current_user.email = email
                    current_user.phone = phone
                    db.session.commit()
                    flash('Profile updated successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while updating your profile. Please try again.', 'error')
                    
        elif action == 'change_password':
            # Get form data
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            # Validation
            errors = []
            
            if not current_password:
                errors.append('Current password is required')
            elif not check_password_hash(current_user.password, current_password):
                errors.append('Current password is incorrect')
                
            if not new_password:
                errors.append('New password is required')
            elif len(new_password) < 6:
                errors.append('New password must be at least 6 characters long')
                
            if new_password != confirm_password:
                errors.append('New passwords do not match')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
            else:
                try:
                    # Update password - new_password is guaranteed to be non-empty string here
                    current_user.password = generate_password_hash(new_password, method='sha256')
                    db.session.commit()
                    flash('Password changed successfully!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('An error occurred while changing your password. Please try again.', 'error')
    
    return render_template('profile_settings.html', user=current_user)
