from flask import Blueprint, render_template
from flask_login import login_required, current_user
from .models import Customer, Laundry, Service
from . import db
from sqlalchemy import func

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def dashboard():
    total_customers = Customer.query.count()
    active_laundries = Laundry.query.filter(Laundry.status != 'Completed').count()
    completed_laundries = Laundry.query.filter_by(status='Completed').count()
    
    # Calculate real revenue from completed laundries
    total_revenue = db.session.query(func.sum(Laundry.price)).filter_by(status='Completed').scalar() or 0
    
    # Calculate estimated revenue from active laundries
    estimated_revenue = db.session.query(func.sum(Laundry.price)).filter(Laundry.status != 'Completed').scalar() or 0
    
    # Service statistics
    total_services = Service.query.count()
    active_services = Service.query.filter_by(is_active=True).count()
    
    # Get popular services (top 3 by laundry count)
    popular_services = db.session.query(
        Service.name, 
        Service.icon,
        Service.category,
        func.count(Laundry.id).label('laundry_count')
    ).join(Laundry, Laundry.service_id == Service.id, isouter=True)\
     .group_by(Service.id)\
     .order_by(func.count(Laundry.id).desc())\
     .limit(3).all()
    
    # Get all active services for pricing display
    all_services = Service.query.filter_by(is_active=True).order_by(Service.category, Service.name).all()
    
    return render_template("dashboard.html", 
                         user=current_user,
                         total_customers=total_customers,
                         active_laundries=active_laundries,
                         completed_laundries=completed_laundries,
                         total_revenue=total_revenue,
                         estimated_revenue=estimated_revenue,
                         total_services=total_services,
                         active_services=active_services,
                         popular_services=popular_services,
                         all_services=all_services)
