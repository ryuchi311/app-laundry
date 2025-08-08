from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Service, Laundry
from . import db
import re

service = Blueprint('service', __name__)

def validate_price(price_str):
    """Validate price format"""
    try:
        price = float(price_str)
        return price >= 0
    except (ValueError, TypeError):
        return False

@service.route('/list')
@login_required
def list_services():
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    category_filter = request.args.get('category', 'all')
    status_filter = request.args.get('status', 'all')
    
    # Start with base query
    query = Service.query
    
    # Apply search filter
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Service.name.ilike(search_term),
                Service.description.ilike(search_term),
                Service.category.ilike(search_term)
            )
        )
    
    # Apply category filter
    if category_filter != 'all':
        query = query.filter(Service.category == category_filter)
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(Service.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(Service.is_active == False)
    
    # Order by category, then by name
    services = query.order_by(Service.category.asc(), Service.name.asc()).all()
    
    # Get all categories for filter dropdown
    categories = db.session.query(Service.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    # Calculate statistics
    total_services = Service.query.count()
    active_services = Service.query.filter(Service.is_active == True).count()
    total_laundries = Laundry.query.count()
    
    return render_template("service_list.html", 
                         user=current_user,
                         services=services,
                         categories=categories,
                         search_query=search_query,
                         category_filter=category_filter,
                         status_filter=status_filter,
                         total_services=total_services,
                         active_services=active_services,
                         total_laundries=total_laundries)

@service.route('/add', methods=['GET', 'POST'])
@login_required
def add_service():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        base_price = request.form.get('base_price')
        price_per_kg = request.form.get('price_per_kg') or '0'
        icon = request.form.get('icon')
        category = request.form.get('category')
        estimated_hours = request.form.get('estimated_hours')
        is_active = request.form.get('is_active') == 'on'

        # Validation
        errors = []
        
        if not name or len(name.strip()) < 2:
            errors.append('Service name must be at least 2 characters long.')
        
        if Service.query.filter_by(name=name.strip()).first():
            errors.append('A service with this name already exists.')
        
        if not base_price or not validate_price(base_price):
            errors.append('Please enter a valid base price.')
        
        if price_per_kg and not validate_price(price_per_kg):
            errors.append('Please enter a valid price per kg.')
        
        if not estimated_hours or not estimated_hours.isdigit() or int(estimated_hours) <= 0:
            errors.append('Please enter a valid estimated completion time in hours.')
        
        if errors:
            for error in errors:
                flash(error, category='error')
        else:
            # Clean and save the data - safe type conversions
            new_service = Service()
            new_service.name = name.strip() if name else ''
            new_service.description = description.strip() if description else None
            new_service.base_price = float(base_price) if base_price else 0.0
            new_service.price_per_kg = float(price_per_kg) if price_per_kg else 0.0
            new_service.icon = icon.strip() if icon else 'fas fa-tshirt'
            new_service.category = category.strip() if category else 'Standard'
            new_service.estimated_hours = int(estimated_hours) if estimated_hours else 1
            new_service.is_active = is_active
            
            db.session.add(new_service)
            db.session.commit()
            flash('Service added successfully!', category='success')
            return redirect(url_for('service.list_services'))

    return render_template("service_add.html", user=current_user)

@service.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_service(id):
    service_obj = Service.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        base_price = request.form.get('base_price')
        price_per_kg = request.form.get('price_per_kg') or '0'
        icon = request.form.get('icon')
        category = request.form.get('category')
        estimated_hours = request.form.get('estimated_hours')
        is_active = request.form.get('is_active') == 'on'
        
        # Validation
        errors = []
        
        if not name or len(name.strip()) < 2:
            errors.append('Service name must be at least 2 characters long.')
        
        # Check for duplicate name (excluding current service)
        existing_service = Service.query.filter_by(name=name.strip()).first()
        if existing_service and existing_service.id != id:
            errors.append('A service with this name already exists.')
        
        if not base_price or not validate_price(base_price):
            errors.append('Please enter a valid base price.')
        
        if price_per_kg and not validate_price(price_per_kg):
            errors.append('Please enter a valid price per kg.')
        
        if not estimated_hours or not estimated_hours.isdigit() or int(estimated_hours) <= 0:
            errors.append('Please enter a valid estimated completion time in hours.')
        
        if errors:
            for error in errors:
                flash(error, category='error')
        else:
            # Update the service - safe type conversions
            service_obj.name = name.strip() if name else ''
            service_obj.description = description.strip() if description else None
            service_obj.base_price = float(base_price) if base_price else 0.0
            service_obj.price_per_kg = float(price_per_kg) if price_per_kg else 0.0
            service_obj.icon = icon.strip() if icon else 'fas fa-tshirt'
            service_obj.category = category.strip() if category else 'Standard'
            service_obj.estimated_hours = int(estimated_hours) if estimated_hours else 1
            service_obj.is_active = is_active
            
            db.session.commit()
            flash('Service updated successfully!', category='success')
            return redirect(url_for('service.list_services'))
    
    return render_template("service_edit.html", user=current_user, service=service_obj)

@service.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_service(id):
    service_obj = Service.query.get_or_404(id)
    
    # Check if service is being used in laundries
    laundries_using_service = Laundry.query.filter_by(service_id=id).count()
    
    if laundries_using_service > 0:
        flash(f'Cannot delete service "{service_obj.name}" because it is being used in {laundries_using_service} laundry item(s). Please deactivate instead.', category='error')
    else:
        db.session.delete(service_obj)
        db.session.commit()
        flash('Service deleted successfully!', category='success')
    
    return redirect(url_for('service.list_services'))

@service.route('/toggle-status/<int:id>', methods=['POST'])
@login_required
def toggle_status(id):
    service_obj = Service.query.get_or_404(id)
    service_obj.is_active = not service_obj.is_active
    db.session.commit()
    
    status = 'activated' if service_obj.is_active else 'deactivated'
    flash(f'Service "{service_obj.name}" has been {status}!', category='success')
    return redirect(url_for('service.list_services'))

@service.route('/api/calculate-price/<int:service_id>')
@login_required
def calculate_price_api(service_id):
    """API endpoint to calculate price for a service"""
    service_obj = Service.query.get_or_404(service_id)
    item_count = request.args.get('items', 1, type=int)
    weight_kg = request.args.get('weight', 0, type=float)
    
    total_price = service_obj.calculate_total_price(item_count, weight_kg)
    
    return jsonify({
        'success': True,
        'service_name': service_obj.name,
        'base_price': service_obj.base_price,
        'price_per_kg': service_obj.price_per_kg,
        'total_price': total_price,
        'estimated_hours': service_obj.estimated_hours
    })
