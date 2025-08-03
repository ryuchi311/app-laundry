from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Customer, Order
from . import db

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def dashboard():
    total_customers = Customer.query.count()
    active_orders = Order.query.filter(Order.status != 'Completed').count()
    completed_orders = Order.query.filter_by(status='Completed').count()
    
    return render_template("dashboard.html", 
                         user=current_user,
                         total_customers=total_customers,
                         active_orders=active_orders,
                         completed_orders=completed_orders)
