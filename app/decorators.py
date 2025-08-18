def user_or_admin_required(f):
    """Decorator to require user, admin, or super_admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_active:
            flash('Your account has been deactivated.', 'error')
            return redirect(url_for('auth.login'))
        if current_user.role not in ['user', 'admin', 'super_admin']:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('views.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def role_required(*allowed_roles):
    """
    Decorator to require specific roles for access to routes.
    Usage: @role_required('admin', 'super_admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            
            if not current_user.is_active:
                flash('Your account has been deactivated.', 'error')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in allowed_roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('views.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin or super_admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Your account has been deactivated.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('Administrator access required.', 'error')
            return redirect(url_for('views.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super_admin role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_active:
            flash('Your account has been deactivated.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_super_admin():
            flash('Super Administrator access required.', 'error')
            return redirect(url_for('views.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function
