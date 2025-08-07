from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Laundry, Customer, LaundryAuditLog, LaundryStatusHistory, User, Service
from . import db, mail
from flask_mail import Message
import random
import string
from datetime import datetime

laundry = Blueprint('laundry', __name__)

def log_laundry_change(laundry_id, action, field_changed=None, old_value=None, new_value=None):
    """Log laundry changes for audit trail"""
    try:
        audit_log = LaundryAuditLog(
            laundry_id=laundry_id,
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

def generate_laundry_id():
    """Generate a unique 10-digit Laundry ID"""
    while True:
        laundry_id = ''.join(random.choices(string.digits, k=10))
        if not Laundry.query.filter_by(laundry_id=laundry_id).first():
            return laundry_id

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

@laundry.route('/list')
@login_required
def list_laundries():
    laundries = Laundry.query.all()
    return render_template("laundries/laundry_list.html", user=current_user, laundries=laundries)

@laundry.route('/add', methods=['GET', 'POST'])
@login_required
def add_laundry():
    if request.method == 'POST':
        customer_id = request.form.get('customerId')
        item_count = request.form.get('itemCount')
        service_type = request.form.get('serviceType')  # This now contains service_id
        weight_kg = request.form.get('weight_kg')
        notes = request.form.get('notes')
        
        customer = Customer.query.get(customer_id)
        if not customer:
            flash('Customer not found!', category='error')
            return redirect(url_for('laundry.add_laundry'))
        
        # Get service details
        service = Service.query.get(service_type)
        if not service:
            flash('Service not found!', category='error')
            return redirect(url_for('laundry.add_laundry'))
            
        new_laundry = Laundry(
            laundry_id=generate_laundry_id(),
            customer_id=customer_id,
            item_count=item_count,
            service_id=service_type,  # Store service_id
            service_type=service.name,  # Store service name for backward compatibility
            weight_kg=float(weight_kg),
            notes=notes,
            status='Received'
        )
        
        # Calculate and set the price
        new_laundry.update_price()
        
        db.session.add(new_laundry)
        db.session.commit()
        
        # Log the Laundry creation
        log_laundry_change(new_laundry.laundry_id, 'CREATED')
        
        # Log initial status in status history
        LaundryStatusHistory.log_status_change(
            laundry_id=new_laundry.laundry_id,
            old_status=None,
            new_status='Received',
            changed_by=current_user.id,
            notes=f"Initial laundry created by {current_user.full_name}"
        )
        db.session.commit()
        
        flash('Laundry created!', category='success')
        # Redirect to edit page for review before printing
        return redirect(url_for('laundry.edit_laundry', laundry_id=new_laundry.laundry_id))
        
    customers = Customer.query.all()
    services = Service.query.filter_by(is_active=True).all()
    return render_template("laundries/laundry_add.html", user=current_user, customers=customers, services=services)

@laundry.route('/receipt/<laundry_id>')
@login_required
def print_receipt(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    return render_template("laundries/laundry_receipt.html", laundry=laundry_item)

@laundry.route('/edit/<laundry_id>', methods=['GET', 'POST'])
@login_required
def edit_laundry(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    
    if request.method == 'POST':
        # Store original values for audit logging
        original_values = {
            'item_count': laundry_item.item_count,
            'service_type': laundry_item.service_type,
            'service_id': laundry_item.service_id,
            'weight_kg': laundry_item.weight_kg,
            'notes': laundry_item.notes,
            'customer_id': laundry_item.customer_id
        }
        
        # Update Laundry fields
        new_item_count = request.form.get('itemCount')
        new_service_type = request.form.get('serviceType')  # This now contains service_id
        new_weight_kg = request.form.get('weight_kg')
        new_notes = request.form.get('notes')
        new_customer_id = request.form.get('customerId')
        
        # Get service details
        service = Service.query.get(new_service_type)
        if not service:
            flash('Service not found!', category='error')
            return redirect(url_for('laundry.edit_laundry', laundry_id=laundry_id))
        
        # Track changes and log them
        changes_made = False
        
        if str(laundry_item.item_count) != new_item_count:
            log_laundry_change(laundry_item.laundry_id, 'EDITED', 'item_count', laundry_item.item_count, new_item_count)
            laundry_item.item_count = new_item_count
            changes_made = True
            
        if laundry_item.service_id != int(new_service_type):
            log_laundry_change(laundry_item.laundry_id, 'EDITED', 'service', 
                           laundry_item.service.name if laundry_item.service else laundry_item.service_type, 
                           service.name)
            laundry_item.service_id = int(new_service_type)
            laundry_item.service_type = service.name  # Update for backward compatibility
            changes_made = True
            
        if laundry_item.weight_kg != float(new_weight_kg):
            log_laundry_change(laundry_item.laundry_id, 'EDITED', 'weight_kg', laundry_item.weight_kg, new_weight_kg)
            laundry_item.weight_kg = float(new_weight_kg)
            changes_made = True
            
        if laundry_item.notes != new_notes:
            log_laundry_change(laundry_item.laundry_id, 'EDITED', 'notes', laundry_item.notes or 'None', new_notes or 'None')
            laundry_item.notes = new_notes
            changes_made = True
        
        # Update customer if changed
        if new_customer_id and int(new_customer_id) != laundry_item.customer_id:
            customer = Customer.query.get(new_customer_id)
            if customer:
                old_customer = Customer.query.get(laundry_item.customer_id)
                log_laundry_change(laundry_item.laundry_id, 'EDITED', 'customer', 
                               old_customer.full_name if old_customer else 'Unknown', 
                               customer.full_name)
                laundry_item.customer_id = new_customer_id
                changes_made = True
        
        # Update tracking fields if changes were made
        if changes_made:
            laundry_item.last_edited_by = current_user.id
            laundry_item.last_edited_at = datetime.utcnow()
            laundry_item.edit_count = (laundry_item.edit_count or 0) + 1
            laundry_item.is_modified = True
            
            # Recalculate price if item count or service type changed
            laundry_item.update_price()
        
        db.session.commit()
        flash('Laundry updated successfully!', category='success')
        
        # Check if user wants to print after editing
        if request.form.get('action') == 'save_and_print':
            return redirect(url_for('laundry.print_receipt', laundry_id=laundry.laundry_id))
        else:
            return redirect(url_for('laundry.list_laundries'))
    
    customers = Customer.query.all()
    services = Service.query.filter_by(is_active=True).all()
    return render_template("laundries/laundry_edit.html", user=current_user, laundry=laundry_item, customers=customers, services=services)

@laundry.route('/update-status/<laundry_id>', methods=['POST'])
@login_required
def update_status(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    new_status = request.form.get('status')
    
    if new_status not in ['Received', 'In Process', 'Ready for Pickup', 'Completed']:
        flash('Invalid status!', category='error')
        return redirect(url_for('laundry.list_laundries'))
    
    # Log status change if status actually changed
    if laundry_item.status != new_status:
        old_status = laundry_item.status
        
        # Log in audit log (legacy)
        log_laundry_change(laundry_item.laundry_id, 'STATUS_CHANGED', 'status', old_status, new_status)
        
        # Log in status history (new detailed tracking)
        LaundryStatusHistory.log_status_change(
            laundry_id=laundry_item.laundry_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
            notes=f"Status changed by {current_user.full_name}"
        )
        
        # Update the laundry status
        laundry_item.status = new_status
        laundry_item.last_edited_by = current_user.id
        laundry_item.last_edited_at = datetime.utcnow()
        laundry_item.edit_count = (laundry_item.edit_count or 0) + 1
        laundry_item.is_modified = True
        
        db.session.commit()
        
        # Send notifications based on status
        if new_status == 'Ready for Pickup':
            send_notification_email(
                laundry_item.customer.email,
                "Pickup ready!",
                f"Your laundry (Laundry #{laundry_item.laundry_id}) is ready for pickup at our location."
            )
        elif new_status == 'Completed':
            # Award loyalty points when order is completed
            from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction
            program = LoyaltyProgram.query.filter_by(is_active=True).first()
            if program:
                try:
                    # Calculate points based on total amount
                    points_earned = int(laundry_item.total_cost * program.points_per_peso)
                    
                    # Get or create customer loyalty record
                    loyalty = CustomerLoyalty.query.filter_by(customer_id=laundry_item.customer_id, program_id=program.id).first()
                    if not loyalty:
                        loyalty = CustomerLoyalty(
                            customer_id=laundry_item.customer_id,
                            program_id=program.id,
                            points_balance=0,
                            total_points_earned=0,
                            total_points_redeemed=0
                        )
                        db.session.add(loyalty)
                    
                    # Award points
                    loyalty.points_balance += points_earned
                    loyalty.total_points_earned += points_earned
                    
                    # Create transaction record
                    transaction = LoyaltyTransaction(
                        customer_id=laundry_item.customer_id,
                        program_id=program.id,
                        laundry_id=laundry_item.laundry_id,
                        transaction_type='earned',
                        points=points_earned,
                        description=f"Points earned from laundry order #{laundry_item.laundry_id}"
                    )
                    db.session.add(transaction)
                    
                    db.session.commit()
                    flash(f'Customer earned {points_earned} loyalty points!', category='info')
                    
                except Exception as e:
                    print(f"Error awarding loyalty points: {e}")
                    db.session.rollback()
        
        flash(f'Laundry status updated to "{new_status}"!', category='success')
    
    return redirect(url_for('laundry.list_laundries'))

@laundry.route('/status-history/<laundry_id>')
@login_required
def view_status_history(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    status_history = LaundryStatusHistory.query.filter_by(laundry_id=laundry_id).order_by(LaundryStatusHistory.changed_at.desc()).all()
    
    return render_template("laundries/laundry_status_history.html", 
                         user=current_user, 
                         laundry=laundry_item, 
                         status_history=status_history)

@laundry.route('/audit/<laundry_id>')
@login_required
def view_audit_log(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    audit_logs = LaundryAuditLog.query.filter_by(laundry_id=laundry_id).order_by(LaundryAuditLog.changed_at.desc()).all()
    
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
    
    return render_template("laundries/laundry_audit.html", user=current_user, laundry=laundry_item, audit_logs=processed_logs)

@laundry.route('/delete/<laundry_id>', methods=['POST'])
@login_required
def delete_laundry(laundry_id):
    laundry_item = Laundry.query.filter_by(laundry_id=laundry_id).first_or_404()
    
    # Log the deletion
    log_laundry_change(laundry_id, 'DELETED', 'Laundry', f"Laundry {laundry_id}", "Deleted")
    
    # Delete associated records first (foreign key constraints)
    LaundryStatusHistory.query.filter_by(laundry_id=laundry_id).delete()
    LaundryAuditLog.query.filter_by(laundry_id=laundry_id).delete()
    
    # Delete the Laundry
    db.session.delete(laundry_item)
    db.session.commit()
    
    flash('Laundry deleted successfully!', category='success')
    return redirect(url_for('laundry.list_laundries'))
