from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import BusinessSettings
from . import db
from functools import wraps

business_settings_bp = Blueprint('business_settings', __name__)

def super_admin_required(f):
    """Decorator to require super admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            flash('Access denied. Super Admin privileges required.', 'error')
            return redirect(url_for('views.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@business_settings_bp.route('/business-settings', methods=['GET', 'POST'])
@login_required
@super_admin_required
def business_settings():
    """Business Settings Configuration Page"""
    settings = BusinessSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update business information
            settings.business_name = request.form.get('business_name', '').strip()
            settings.business_tagline = request.form.get('business_tagline', '').strip()
            settings.business_description = request.form.get('business_description', '').strip()
            
            # Update contact information
            settings.phone = request.form.get('phone', '').strip()
            settings.email = request.form.get('email', '').strip()
            settings.address = request.form.get('address', '').strip()
            settings.operating_hours = request.form.get('operating_hours', '').strip()
            
            # Update footer information
            settings.footer_text = request.form.get('footer_text', '').strip()
            settings.copyright_text = request.form.get('copyright_text', '').strip()
            
            # Update social media links
            settings.facebook_url = request.form.get('facebook_url', '').strip()
            settings.instagram_url = request.form.get('instagram_url', '').strip()
            settings.website_url = request.form.get('website_url', '').strip()
            
            # Update system settings
            settings.currency_symbol = request.form.get('currency_symbol', '₱').strip()
            settings.timezone = request.form.get('timezone', 'Asia/Manila').strip()
            
            # Update metadata
            settings.updated_by = current_user.id
            
            db.session.commit()
            flash('Business settings updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating business settings: {str(e)}', 'error')
    
    return render_template('business_settings.html', settings=settings)

@business_settings_bp.route('/business-settings/preview', methods=['POST'])
@login_required
@super_admin_required
def preview_changes():
    """API endpoint to preview business settings changes"""
    try:
        data = request.get_json()
        
        return jsonify({
            'success': True,
            'preview': {
                'business_name': data.get('business_name', 'ACCIO'),
                'business_tagline': data.get('business_tagline', 'Labhonon Laundry'),
                'footer_text': data.get('footer_text', 'Quality laundry services you can trust'),
                'copyright_text': data.get('copyright_text', '© 2025 ACCIO Labhonon Laundry. All rights reserved.')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@business_settings_bp.route('/api/business-info')
def get_business_info():
    """API endpoint to get current business information"""
    try:
        settings = BusinessSettings.get_settings()
        
        return jsonify({
            'business_name': settings.business_name,
            'business_tagline': settings.business_tagline,
            'phone': settings.phone,
            'email': settings.email,
            'address': settings.address,
            'footer_text': settings.footer_text,
            'copyright_text': settings.copyright_text
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        })
