from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Order, Customer
from . import db, mail
from flask_mail import Message
import random
import string
from datetime import datetime

order = Blueprint('order', __name__)

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
        flash('Order created!', category='success')
        return redirect(url_for('order.list_orders'))
        
    customers = Customer.query.all()
    return render_template("order_add.html", user=current_user, customers=customers)

@order.route('/update-status/<order_id>', methods=['POST'])
@login_required
def update_status(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    new_status = request.form.get('status')
    
    if new_status not in ['Received', 'In Process', 'Ready for Pickup', 'Completed']:
        flash('Invalid status!', category='error')
        return redirect(url_for('order.list_orders'))
        
    order.status = new_status
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
