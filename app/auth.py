from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from .models import User
from . import db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill in all fields.', category='error')
            return render_template("login.html", user=current_user)

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                # Check if user can login (approved and active)
                if not user.can_login():
                    if user.is_pending_approval():
                        flash('Your account is pending approval from a Super Administrator. Please wait for approval.', category='warning')
                    elif not user.is_active:
                        flash('Your account has been deactivated. Please contact the administrator.', category='error')
                    else:
                        flash('Access denied. Please contact the administrator.', category='error')
                    return render_template("login.html", user=current_user)
                
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.dashboard'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        full_name = request.form.get('fullName')
        phone = request.form.get('phone')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Check for None values first
        if not email or not full_name or not password1 or not password2:
            flash('Please fill in all required fields.', category='error')
            return render_template("signup.html", user=current_user)

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(full_name) < 2:
            flash('Full name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            # Check if this is the first user (make them super admin)
            user_count = User.query.count()
            is_first_user = user_count == 0
            
            # Create new user with proper attribute assignment
            new_user = User()
            new_user.email = email
            new_user.full_name = full_name
            new_user.phone = phone
            new_user.password = generate_password_hash(password1, method='pbkdf2:sha256')
            new_user.role = 'super_admin' if is_first_user else 'employee'
            new_user.is_active = True
            new_user.is_approved = True if is_first_user else False  # First user auto-approved
            
            db.session.add(new_user)
            db.session.commit()
            
            if is_first_user:
                login_user(new_user, remember=True)
                flash('Account created! You are now the Super Administrator.', category='success')
                return redirect(url_for('views.dashboard'))
            else:
                flash('Account created successfully! Please wait for a Super Administrator to approve your account before you can log in.', category='success')
                return redirect(url_for('auth.login'))

    return render_template("signup.html", user=current_user)
