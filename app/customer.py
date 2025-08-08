from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, make_response
from flask_login import login_required, current_user
from .models import Customer
from . import db
from .sms_service import send_welcome_sms
import csv
import io
import re

customer = Blueprint('customer', __name__)

def validate_phone_number(phone):
    """Validate Philippine phone number format"""
    if not phone:
        return False
    # Allow +639XXXXXXXXX or 09XXXXXXXXX formats
    phone_pattern = r'^(\+63|0)[0-9]{10}$'
    return bool(re.match(phone_pattern, phone))

def validate_email(email):
    """Validate email format"""
    if not email:
        return True  # Email is optional
    email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    return bool(re.match(email_pattern, email, re.IGNORECASE))

@customer.route('/list')
@login_required
def list_customers():
    # Get search and pagination parameters
    search_query = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Fixed limit of 10 customers per page
    sort_by = request.args.get('sort_by', 'name')  # name, email, date_created
    sort_order = request.args.get('sort_order', 'asc')  # asc, desc
    
    # Start with base query
    query = Customer.query
    
    # Apply search filter (search across name, email, and phone)
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == 'name':
        if sort_order == 'desc':
            query = query.order_by(Customer.full_name.desc())
        else:
            query = query.order_by(Customer.full_name.asc())
    elif sort_by == 'email':
        if sort_order == 'desc':
            query = query.order_by(Customer.email.desc())
        else:
            query = query.order_by(Customer.email.asc())
    elif sort_by == 'date_created':
        if sort_order == 'desc':
            query = query.order_by(Customer.date_created.desc())
        else:
            query = query.order_by(Customer.date_created.asc())
    else:  # Default to name
        query = query.order_by(Customer.full_name.asc())
    
    # Apply pagination
    customers = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Get total customer count for display
    total_customers = Customer.query.count()
    
    return render_template("customer_list.html", 
                         user=current_user, 
                         customers=customers,
                         total_customers=total_customers,
                         search_query=search_query,
                         sort_by=sort_by,
                         sort_order=sort_order)

@customer.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Validation
        errors = []
        
        if not full_name or len(full_name.strip()) < 2:
            errors.append('Full name must be at least 2 characters long.')
        
        if not phone or not validate_phone_number(phone):
            errors.append('Please enter a valid Philippine phone number (e.g., +639123456789 or 09123456789).')
        
        if email and not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        if errors:
            for error in errors:
                flash(error, category='error')
        else:
            # Clean the data
            full_name = full_name.strip()
            email = email.strip() if email else None
            phone = phone.strip()
            
            # Create new customer with proper attribute assignment
            new_customer = Customer()
            new_customer.full_name = full_name
            new_customer.email = email
            new_customer.phone = phone
            
            db.session.add(new_customer)
            db.session.commit()
            
            # Send welcome SMS if phone number is provided
            if phone:
                send_welcome_sms(new_customer)
            
            flash('Customer added successfully!', category='success')
            return redirect(url_for('customer.list_customers'))

    return render_template("customer_add.html", user=current_user)

@customer.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer_obj = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # Validation
        errors = []
        
        if not full_name or len(full_name.strip()) < 2:
            errors.append('Full name must be at least 2 characters long.')
        
        if not phone or not validate_phone_number(phone):
            errors.append('Please enter a valid Philippine phone number (e.g., +639123456789 or 09123456789).')
        
        if email and not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        if errors:
            for error in errors:
                flash(error, category='error')
        else:
            # Clean and update the data
            customer_obj.full_name = full_name.strip()
            customer_obj.email = email.strip() if email else None
            customer_obj.phone = phone.strip()
            
            db.session.commit()
            flash('Customer updated successfully!', category='success')
            return redirect(url_for('customer.list_customers'))
        
    return render_template("customer_edit.html", user=current_user, customer=customer_obj)

@customer.route('/delete/<int:id>')
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted!', category='success')
    return redirect(url_for('customer.list_customers'))

@customer.route('/export')
@login_required
def export_customers():
    # Get the same filters as list_customers
    search_query = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'name')
    sort_order = request.args.get('sort_order', 'asc')
    
    # Start with base query
    query = Customer.query
    
    # Apply search filter
    if search_query:
        search_term = f'%{search_query}%'
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.phone.ilike(search_term)
            )
        )
    
    # Apply sorting
    if sort_by == 'name':
        if sort_order == 'desc':
            query = query.order_by(Customer.full_name.desc())
        else:
            query = query.order_by(Customer.full_name.asc())
    elif sort_by == 'email':
        if sort_order == 'desc':
            query = query.order_by(Customer.email.desc())
        else:
            query = query.order_by(Customer.email.asc())
    elif sort_by == 'date_created':
        if sort_order == 'desc':
            query = query.order_by(Customer.date_created.desc())
        else:
            query = query.order_by(Customer.date_created.asc())
    else:
        query = query.order_by(Customer.full_name.asc())
    
    # Get all customers (no pagination for export)
    customers = query.all()
    
    # Create CSV file in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Full Name', 'Email', 'Phone', 'Date Created'])
    
    # Write customer data
    for customer in customers:
        writer.writerow([
            customer.id,
            customer.full_name,
            customer.email or '',
            customer.phone or '',
            customer.date_created.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=customers.csv'
    
    return response
