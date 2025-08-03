from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Customer
from . import db

customer = Blueprint('customer', __name__)

@customer.route('/list')
@login_required
def list_customers():
    customers = Customer.query.all()
    return render_template("customer_list.html", user=current_user, customers=customers)

@customer.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        phone = request.form.get('phone')

        if len(full_name) < 2:
            flash('Full name is too short!', category='error')
        else:
            new_customer = Customer(full_name=full_name, email=email, phone=phone)
            db.session.add(new_customer)
            db.session.commit()
            flash('Customer added!', category='success')
            return redirect(url_for('customer.list_customers'))

    return render_template("customer_add.html", user=current_user)

@customer.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        customer.full_name = request.form.get('fullName')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        
        db.session.commit()
        flash('Customer updated!', category='success')
        return redirect(url_for('customer.list_customers'))
        
    return render_template("customer_edit.html", user=current_user, customer=customer)

@customer.route('/delete/<int:id>')
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    flash('Customer deleted!', category='success')
    return redirect(url_for('customer.list_customers'))
