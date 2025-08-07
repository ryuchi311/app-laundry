from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from . import db
from datetime import datetime

loyalty_bp = Blueprint('loyalty_bp', __name__)

@loyalty_bp.route('/dashboard')
@login_required
def dashboard():
    # Import models here to avoid circular import issues
    from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, Customer
    from sqlalchemy import func
    
    # Get program stats
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    
    stats = {
        'total_members': CustomerLoyalty.query.count(),
        'total_points_earned': db.session.query(func.sum(CustomerLoyalty.total_points_earned)).scalar() or 0,
        'total_points_redeemed': db.session.query(func.sum(CustomerLoyalty.total_points_redeemed)).scalar() or 0,
        'active_members': CustomerLoyalty.query.filter(CustomerLoyalty.current_points > 0).count()
    }
    
    # Get recent transactions
    recent_transactions = LoyaltyTransaction.query.order_by(LoyaltyTransaction.created_at.desc()).limit(5).all()
    
    # Get all customers for modal
    customers = Customer.query.all()
    
    return render_template('loyalty/dashboard.html', 
                         program=program, 
                         stats=stats, 
                         recent_transactions=recent_transactions,
                         customers=customers)

@loyalty_bp.route('/customers')
@login_required
def customers():
    from .models import Customer, CustomerLoyalty
    
    # Get query parameters
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'name')
    page = request.args.get('page', 1, type=int)
    
    # Start with base query
    query = Customer.query
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%')
            )
        )
    
    # Apply sorting
    if sort_by == 'name':
        query = query.order_by(Customer.full_name)
    elif sort_by == 'joined':
        query = query.order_by(Customer.date_created.desc())
    
    # Paginate
    customers = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('loyalty/customers.html', customers=customers)

@loyalty_bp.route('/customer/<int:customer_id>')
@login_required
def customer_detail(customer_id):
    from .models import Customer, CustomerLoyalty, LoyaltyTransaction
    
    customer = Customer.query.get_or_404(customer_id)
    loyalty = CustomerLoyalty.query.filter_by(customer_id=customer_id).first()
    
    if not loyalty:
        loyalty = CustomerLoyalty(customer_id=customer_id)
        db.session.add(loyalty)
        db.session.commit()
    
    # Get customer's transaction history
    transactions = LoyaltyTransaction.query.filter_by(customer_loyalty_id=loyalty.id).order_by(LoyaltyTransaction.created_at.desc()).all()
    
    return render_template('loyalty/customer_detail.html', customer=customer, loyalty=loyalty, transactions=transactions)

@loyalty_bp.route('/settings')
@login_required
def settings():
    from .models import LoyaltyProgram
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    return render_template('loyalty/settings.html', program=program)

@loyalty_bp.route('/settings', methods=['POST'])
@login_required
def update_settings():
    from .models import LoyaltyProgram
    
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    
    if not program:
        # Create new program
        program = LoyaltyProgram(
            name=request.form.get('name'),
            points_per_peso=float(request.form.get('points_per_peso', 1.0)),
            peso_per_point=float(request.form.get('peso_per_point', 1.0)),
            is_active=True
        )
        db.session.add(program)
    else:
        # Update existing program
        program.name = request.form.get('name')
        program.points_per_peso = float(request.form.get('points_per_peso', 1.0))
        program.peso_per_point = float(request.form.get('peso_per_point', 1.0))
    
    try:
        db.session.commit()
        flash('Loyalty program settings updated successfully!', category='success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', category='error')
    
    return redirect(url_for('loyalty_bp.settings'))

@loyalty_bp.route('/award_points', methods=['POST'])
@login_required
def award_points():
    from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, Customer
    
    customer_id = int(request.form.get('customer_id'))
    points = int(request.form.get('points'))
    reason = request.form.get('reason', 'Manual award')
    
    customer = Customer.query.get_or_404(customer_id)
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    
    if not program:
        flash('No active loyalty program found!', category='error')
        return redirect(request.referrer or url_for('loyalty_bp.dashboard'))
    
    try:
        # Get or create loyalty record
        loyalty = CustomerLoyalty.query.filter_by(customer_id=customer_id).first()
        if not loyalty:
            loyalty = CustomerLoyalty(
                customer_id=customer_id,
                current_points=0,
                total_points_earned=0,
                total_points_redeemed=0
            )
            db.session.add(loyalty)
        
        # Award points
        loyalty.current_points += points
        loyalty.total_points_earned += points
        
        # Create transaction record
        transaction = LoyaltyTransaction(
            customer_loyalty_id=loyalty.id,
            transaction_type='EARNED',
            points=points,
            description=reason
        )
        db.session.add(transaction)
        
        db.session.commit()
        flash(f'Successfully awarded {points} points to {customer.full_name}!', category='success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error awarding points: {str(e)}', category='error')
    
    return redirect(request.referrer or url_for('loyalty_bp.dashboard'))

@loyalty_bp.route('/redeem_points', methods=['POST'])
@login_required
def redeem_points():
    from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, Customer
    
    customer_id = int(request.form.get('customer_id'))
    points = int(request.form.get('points'))
    reason = request.form.get('reason', 'Points redemption')
    
    customer = Customer.query.get_or_404(customer_id)
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    
    if not program:
        flash('No active loyalty program found!', category='error')
        return redirect(request.referrer or url_for('loyalty_bp.dashboard'))
    
    try:
        # Get loyalty record
        loyalty = CustomerLoyalty.query.filter_by(customer_id=customer_id).first()
        if not loyalty or loyalty.current_points < points:
            flash('Insufficient points balance!', category='error')
            return redirect(request.referrer or url_for('loyalty_bp.dashboard'))
        
        # Redeem points
        loyalty.current_points -= points
        loyalty.total_points_redeemed += points
        
        # Create transaction record
        transaction = LoyaltyTransaction(
            customer_loyalty_id=loyalty.id,
            transaction_type='REDEEMED',
            points=-points,  # Negative for redemption
            description=reason
        )
        db.session.add(transaction)
        
        db.session.commit()
        flash(f'Successfully redeemed {points} points from {customer.full_name}!', category='success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error redeeming points: {str(e)}', category='error')
    
    return redirect(request.referrer or url_for('loyalty_bp.dashboard'))

@loyalty_bp.route('/reset_all_points', methods=['POST'])
@login_required
def reset_all_points():
    from .models import CustomerLoyalty, LoyaltyTransaction
    
    try:
        # Reset all customer points to zero
        CustomerLoyalty.query.update({
            'current_points': 0,
            'total_points_redeemed': CustomerLoyalty.total_points_earned
        })
        
        # Create reset transactions for all customers
        customers_with_loyalty = CustomerLoyalty.query.all()
        for loyalty in customers_with_loyalty:
            if loyalty.current_points > 0:
                transaction = LoyaltyTransaction(
                    customer_loyalty_id=loyalty.id,
                    transaction_type='RESET',
                    points=-loyalty.current_points,
                    description='Admin reset - all points cleared'
                )
                db.session.add(transaction)
        
        db.session.commit()
        flash('All customer points have been reset to zero!', category='success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting points: {str(e)}', category='error')
    
    return redirect(url_for('loyalty_bp.settings'))

@loyalty_bp.route('/delete_program', methods=['POST'])
@login_required
def delete_program():
    from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction
    
    confirm_text = request.form.get('confirm_text', '').strip()
    if confirm_text != 'DELETE':
        flash('Please type "DELETE" to confirm program deletion.', category='error')
        return redirect(url_for('loyalty_bp.settings'))
    
    try:
        # Delete all loyalty transactions
        LoyaltyTransaction.query.delete()
        
        # Delete all customer loyalty records
        CustomerLoyalty.query.delete()
        
        # Delete the loyalty program
        LoyaltyProgram.query.delete()
        
        db.session.commit()
        flash('Loyalty program has been permanently deleted!', category='success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting program: {str(e)}', category='error')
    
    return redirect(url_for('loyalty_bp.settings'))
