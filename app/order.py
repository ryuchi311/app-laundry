from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Order, Customer, OrderAuditLog, User
from . import db, mail
from flask_mail import Message
import random
import string
from datetime import datetime

order = Blueprint('order', __name__)

def log_order_change(order_id, action, field_changed=None, old_value=None, new_value=None):
    """Log order changes for audit trail"""
    try:
        audit_log = OrderAuditLog(
            order_id=order_id,
            action=action,
            field_changed=field_changed,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            changed_by=current_user.id,
            ip_address=request.remote_addr
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")

def generate_order_id():
    """Generate a unique 10-digit order ID"""
    while True:
        order_id = ''.join(random.choices(string.digits, k=10))
        if not Order.query.filter_by(order_id=order_id).first():
            return order_id

def send_notification_email(customer_email, subject, body):
    """Send email notification to customer"""
    try:
        msg = Message(subject,
                     sender='noreply@acciolaundry.com',
                     recipients=[customer_email])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@order.route('/list')
@login_required
def list_orders():
    orders = Order.query.all()
    return render_template("order_list.html", user=current_user, orders=orders)

@order.route('/add', methods=['GET', 'POST'])
@login_required
def add_order():
    if request.method == 'POST':
        customer_id = request.form.get('customerId')
        item_count = request.form.get('itemCount')
        service_type = request.form.get('serviceType')
        notes = request.form.get('notes')
        
        customer = Customer.query.get(customer_id)
        if not customer:
            flash('Customer not found!', category='error')
            return redirect(url_for('order.add_order'))
            
        new_order = Order(
            order_id=generate_order_id(),
            customer_id=customer_id,
            item_count=item_count,
            service_type=service_type,
            notes=notes,
            status='Received'
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # Log the order creation
        log_order_change(new_order.order_id, 'CREATED')
        
        flash('Order created!', category='success')
        # Redirect to edit page for review before printing
        return redirect(url_for('order.edit_order', order_id=new_order.order_id))
        
    customers = Customer.query.all()
    return render_template("order_add.html", user=current_user, customers=customers)

@order.route('/receipt/<order_id>')
@login_required
def print_receipt(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    return render_template("order_receipt.html", order=order)

@order.route('/edit/<order_id>', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    
    if request.method == 'POST':
        # Store original values for audit logging
        original_values = {
            'item_count': order.item_count,
            'service_type': order.service_type,
            'notes': order.notes,
            'customer_id': order.customer_id
        }
        
        # Update order fields
        new_item_count = request.form.get('itemCount')
        new_service_type = request.form.get('serviceType')
        new_notes = request.form.get('notes')
        new_customer_id = request.form.get('customerId')
        
        # Track changes and log them
        changes_made = False
        
        if str(order.item_count) != new_item_count:
            log_order_change(order.order_id, 'EDITED', 'item_count', order.item_count, new_item_count)
            order.item_count = new_item_count
            changes_made = True
            
        if order.service_type != new_service_type:
            log_order_change(order.order_id, 'EDITED', 'service_type', order.service_type, new_service_type)
            order.service_type = new_service_type
            changes_made = True
            
        if order.notes != new_notes:
            log_order_change(order.order_id, 'EDITED', 'notes', order.notes or 'None', new_notes or 'None')
            order.notes = new_notes
            changes_made = True
        
        # Update customer if changed
        if new_customer_id and int(new_customer_id) != order.customer_id:
            customer = Customer.query.get(new_customer_id)
            if customer:
                old_customer = Customer.query.get(order.customer_id)
                log_order_change(order.order_id, 'EDITED', 'customer', 
                               old_customer.full_name if old_customer else 'Unknown', 
                               customer.full_name)
                order.customer_id = new_customer_id
                changes_made = True
        
        # Update tracking fields if changes were made
        if changes_made:
            order.last_edited_by = current_user.id
            order.last_edited_at = datetime.utcnow()
            order.edit_count = (order.edit_count or 0) + 1
            order.is_modified = True
        
        db.session.commit()
        flash('Order updated successfully!', category='success')
        
        # Check if user wants to print after editing
        if request.form.get('action') == 'save_and_print':
            return redirect(url_for('order.print_receipt', order_id=order.order_id))
        else:
            return redirect(url_for('order.list_orders'))
    
    customers = Customer.query.all()
    return render_template("order_edit.html", user=current_user, order=order, customers=customers)

@order.route('/update-status/<order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    new_status = request.form.get('status')
    
    if new_status not in ['Received', 'In Process', 'Ready for Pickup', 'Completed']:
        flash('Invalid status!', category='error')
        return redirect(url_for('order.list_orders'))
    
    # Log status change
    if order.status != new_status:
        log_order_change(order.order_id, 'STATUS_CHANGED', 'status', order.status, new_status)
        order.status = new_status
        order.last_edited_by = current_user.id
        order.last_edited_at = datetime.utcnow()
        order.edit_count = (order.edit_count or 0) + 1
        order.is_modified = True
        
        db.session.commit()
        
        # Send notifications based on status
        if new_status == 'Ready for Pickup':
            send_notification_email(
                order.customer.email,
                "Pickup ready!",
                f"Your laundry (Order #{order.order_id}) is ready for pickup at our location."
            )
        
        flash('Order status updated!', category='success')
    
    return redirect(url_for('order.list_orders'))

@order.route('/audit/<order_id>')
@login_required
def view_audit_log(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    audit_logs = OrderAuditLog.query.filter_by(order_id=order_id).order_by(OrderAuditLog.changed_at.desc()).all()
    
    # Process audit logs to group by action and add user info
    processed_logs = []
    for log in audit_logs:
        user = User.query.get(log.changed_by)
        processed_logs.append({
            'id': log.id,
            'action': log.action,
            'field_changed': log.field_changed,
            'old_value': log.old_value,
            'new_value': log.new_value,
            'timestamp': log.changed_at,
            'user_email': user.email if user else 'Unknown User',
            'ip_address': log.ip_address
        })
    
    return render_template("order_audit.html", user=current_user, order=order, audit_logs=processed_logs)
