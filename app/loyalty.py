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
    
    # Get program stats
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    
    stats = {
        'total_members': CustomerLoyalty.query.count(),
        'total_points_earned': db.session.query(db.func.sum(CustomerLoyalty.total_points_earned)).scalar() or 0,
        'total_points_redeemed': db.session.query(db.func.sum(CustomerLoyalty.total_points_redeemed)).scalar() or 0,
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
    from .models import Customer, LoyaltyTransaction, CustomerLoyalty

    customer = Customer.query.get_or_404(customer_id)

    # Customer transactions via loyalty join
    page = request.args.get('page', 1, type=int)
    transactions = (
        LoyaltyTransaction.query
        .join(CustomerLoyalty, LoyaltyTransaction.customer_loyalty_id == CustomerLoyalty.id)
        .filter(CustomerLoyalty.customer_id == customer_id)
        .order_by(LoyaltyTransaction.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )

    return render_template('loyalty/customer_detail.html', 
                         customer=customer,
                         transactions=transactions)

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
    
    name = request.form.get('name', '').strip()
    points_per_peso = float(request.form.get('points_per_peso', 1))
    # UI collects points-per-₱ discount; convert to peso_per_point
    try:
        ppd_val = int(request.form.get('points_per_peso_discount', 100))
    except (TypeError, ValueError):
        ppd_val = 100
    tier_thresholds = request.form.get('tier_thresholds', '').strip()
    is_active = 'is_active' in request.form
    
    if not name:
        flash('Program name is required!', category='error')
        return redirect(url_for('loyalty_bp.settings'))
    
    try:
        # Get existing program or create new one
        program = LoyaltyProgram.query.filter_by(is_active=True).first()
        if not program:
            program = LoyaltyProgram()
            db.session.add(program)
        
        # Update program settings
        program.name = name
        program.points_per_peso = points_per_peso
        # Convert points-per-₱ to peso value per point
        program.peso_per_point = (1.0 / ppd_val) if ppd_val and ppd_val > 0 else program.peso_per_point
        program.is_active = is_active

        # Parse tier thresholds (Bronze, Silver, Gold, Platinum)
        if tier_thresholds:
            try:
                parts = [int(x.strip()) for x in tier_thresholds.split(',') if x.strip() != '']
                # Map parts to model fields if provided
                if len(parts) >= 1: program.bronze_threshold = parts[0]
                if len(parts) >= 2: program.silver_threshold = parts[1]
                if len(parts) >= 3: program.gold_threshold = parts[2]
                if len(parts) >= 4: program.platinum_threshold = parts[3]
            except Exception:
                pass
        
        db.session.commit()
        flash('Loyalty program settings updated successfully!', category='success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating settings: {str(e)}', category='error')
    
    return redirect(url_for('loyalty_bp.settings'))

@loyalty_bp.route('/award_points', methods=['POST'])
@login_required
def award_points():
    from .models import Customer, LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction
    
    customer_id = request.form.get('customer_id')
    points = int(request.form.get('points', 0))
    reason = request.form.get('reason', 'Manual award')
    
    if points <= 0:
        flash('Points must be greater than zero!', category='error')
        return redirect(request.referrer or url_for('loyalty_bp.dashboard'))
    
    customer = Customer.query.get_or_404(customer_id)
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    
    if not program:
        flash('No active loyalty program found!', category='error')
        return redirect(request.referrer or url_for('loyalty_bp.dashboard'))
    
    try:
        # Get or create loyalty record
        loyalty = CustomerLoyalty.query.filter_by(customer_id=customer_id).first()
        if not loyalty:
            loyalty = CustomerLoyalty()
            loyalty.customer_id = customer_id
            loyalty.current_points = 0
            loyalty.total_points_earned = 0
            loyalty.total_points_redeemed = 0
            db.session.add(loyalty)

        # Award points
        loyalty.current_points += points
        loyalty.total_points_earned += points

        # Create transaction record
        transaction = LoyaltyTransaction()
        transaction.customer_loyalty_id = loyalty.id
        transaction.transaction_type = 'EARNED'
        transaction.points = points
        transaction.description = reason
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
    from .models import Customer, LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction
    
    customer_id = request.form.get('customer_id')
    points = int(request.form.get('points', 0))
    reason = request.form.get('reason', 'Points redeemed')
    
    if points <= 0:
        flash('Points must be greater than zero!', category='error')
        return redirect(request.referrer or url_for('loyalty_bp.dashboard'))
    
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
        transaction = LoyaltyTransaction()
        transaction.customer_loyalty_id = loyalty.id
        transaction.transaction_type = 'REDEEMED'
        transaction.points = -points  # Negative for redemption
        transaction.description = reason
        db.session.add(transaction)

        db.session.commit()
        flash(f'Successfully redeemed {points} points from {customer.full_name}!', category='success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error redeeming points: {str(e)}', category='error')
    
    return redirect(request.referrer or url_for('loyalty_bp.dashboard'))

@loyalty_bp.route('/bulk_award_points', methods=['POST'])
@login_required
def bulk_award_points():
    from .models import LoyaltyProgram, CustomerLoyalty, LoyaltyTransaction, Customer
    
    award_to = request.form.get('award_to')
    points_str = request.form.get('points', '0')
    try:
        points = int(points_str) if points_str else 0
    except ValueError:
        points = 0
    reason = request.form.get('reason', 'Bulk award')
    
    program = LoyaltyProgram.query.filter_by(is_active=True).first()
    if not program:
        flash('No active loyalty program found!', category='error')
        return redirect(url_for('loyalty_bp.customers'))
    
    try:
        customers_awarded = 0
        total_points_awarded = 0
        
        if award_to == 'all':
            # Award to all customers
            customers = Customer.query.all()
        else:
            # For tier-based awards, we'll award to all customers for now
            # since we don't have tier implementation yet
            customers = Customer.query.all()
        
        for customer in customers:
            # Get or create loyalty record
            loyalty = CustomerLoyalty.query.filter_by(customer_id=customer.id).first()
            if not loyalty:
                loyalty = CustomerLoyalty()
                loyalty.customer_id = customer.id
                loyalty.current_points = 0
                loyalty.total_points_earned = 0
                loyalty.total_points_redeemed = 0
                db.session.add(loyalty)
            
            # Award points
            loyalty.current_points += points
            loyalty.total_points_earned += points
            
            # Create transaction record
            transaction = LoyaltyTransaction()
            transaction.customer_loyalty_id = loyalty.id
            transaction.transaction_type = 'EARNED'
            transaction.points = points
            transaction.description = f'{reason} (Bulk Award)'
            db.session.add(transaction)
            
            customers_awarded += 1
            total_points_awarded += points
        
        db.session.commit()
        flash(f'Successfully awarded {points} points to {customers_awarded} customers! Total points awarded: {total_points_awarded}', category='success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error in bulk award: {str(e)}', category='error')
    
    return redirect(url_for('loyalty_bp.customers'))

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
                transaction = LoyaltyTransaction()
                transaction.customer_loyalty_id = loyalty.id
                transaction.transaction_type = 'RESET'
                transaction.points = -loyalty.current_points
                transaction.description = 'Admin reset - all points cleared'
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
    
    # Align with template input name
    confirm_text = request.form.get('confirmation', '').strip()
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
