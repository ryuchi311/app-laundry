from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import json
from .models import db, Expense, ExpenseCategory, SalesReport, Laundry, Customer, InventoryItem, StockMovement, LaundryStatusHistory, Service

expenses_bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@expenses_bp.route('/')
@login_required
def dashboard():
    """Expense dashboard with overview"""
    # Current month expenses
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Get monthly expenses
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        and_(
            Expense.expense_date >= start_of_month,
            Expense.expense_date <= today
        )
    ).scalar() or 0
    
    # Get monthly revenue (from laundries)
    monthly_revenue = db.session.query(func.sum(Laundry.price)).filter(
        and_(
            Laundry.date_received >= start_of_month,
            Laundry.date_received <= today
        )
    ).scalar() or 0
    
    # Recent expenses
    recent_expenses = Expense.query.order_by(Expense.created_at.desc()).limit(10).all()
    
    # Expense by category this month
    category_expenses = db.session.query(
        ExpenseCategory.name,
        ExpenseCategory.color,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        and_(
            Expense.expense_date >= start_of_month,
            Expense.expense_date <= today
        )
    ).group_by(ExpenseCategory.name, ExpenseCategory.color).all()
    
    # Pending recurring expenses
    upcoming_expenses = Expense.query.filter(
        and_(
            Expense.is_recurring == True,
            Expense.next_due_date <= today + timedelta(days=7)
        )
    ).limit(5).all()
    
    return render_template('expenses/dashboard.html',
                         monthly_expenses=monthly_expenses,
                         monthly_revenue=monthly_revenue,
                         net_profit=monthly_revenue - monthly_expenses,
                         recent_expenses=recent_expenses,
                         category_expenses=category_expenses,
                         upcoming_expenses=upcoming_expenses)

@expenses_bp.route('/list')
@login_required
def list_expenses():
    """List all expenses with filtering"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    expense_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    query = Expense.query
    
    # Apply filters
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    
    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Expense.expense_date <= date_to_obj)
        except ValueError:
            pass
    
    if search:
        query = query.filter(or_(
            Expense.title.ilike(f'%{search}%'),
            Expense.description.ilike(f'%{search}%'),
            Expense.vendor.ilike(f'%{search}%')
        ))
    
    expenses = query.order_by(Expense.expense_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    categories = ExpenseCategory.query.filter(ExpenseCategory.is_active == True).all()
    
    return render_template('expenses/list.html',
                         expenses=expenses,
                         categories=categories)

@expenses_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    """Add new expense"""
    if request.method == 'POST':
        try:
            # Create new expense with proper attribute assignment
            expense = Expense()
            expense.title = request.form['title']
            expense.description = request.form.get('description', '')
            expense.amount = float(request.form['amount'])
            expense.category_id = int(request.form['category_id'])
            expense.expense_date = datetime.strptime(request.form['expense_date'], '%Y-%m-%d').date()
            expense.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date() if request.form.get('due_date') else None
            expense.expense_type = request.form.get('expense_type', 'ONE_TIME')
            expense.payment_method = request.form.get('payment_method', '')
            expense.payment_status = request.form.get('payment_status', 'PAID')
            expense.vendor = request.form.get('vendor', '')
            expense.invoice_number = request.form.get('invoice_number', '')
            expense.receipt_number = request.form.get('receipt_number', '')
            expense.is_recurring = request.form.get('is_recurring') == 'on'
            expense.recurring_frequency = request.form.get('recurring_frequency', '')
            expense.created_by = current_user.id
            
            # Set next due date for recurring expenses
            if expense.is_recurring and expense.recurring_frequency:
                if expense.recurring_frequency == 'MONTHLY':
                    expense.next_due_date = expense.expense_date + timedelta(days=30)
                elif expense.recurring_frequency == 'QUARTERLY':
                    expense.next_due_date = expense.expense_date + timedelta(days=90)
                elif expense.recurring_frequency == 'YEARLY':
                    expense.next_due_date = expense.expense_date + timedelta(days=365)
            
            expense.generate_expense_id()
            db.session.add(expense)
            db.session.commit()
            
            flash(f'Expense {expense.expense_id} added successfully!', 'success')
            return redirect(url_for('expenses.list_expenses'))
            
        except Exception as e:
            flash(f'Error adding expense: {str(e)}', 'error')
            db.session.rollback()
    
    categories = ExpenseCategory.query.filter(ExpenseCategory.is_active == True).all()
    return render_template('expenses/form.html', categories=categories)

@expenses_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    """Edit existing expense"""
    expense = Expense.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            expense.title = request.form['title']
            expense.description = request.form.get('description', '')
            expense.amount = float(request.form['amount'])
            expense.category_id = int(request.form['category_id'])
            expense.expense_date = datetime.strptime(request.form['expense_date'], '%Y-%m-%d').date()
            expense.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date() if request.form.get('due_date') else None
            expense.expense_type = request.form.get('expense_type', 'ONE_TIME')
            expense.payment_method = request.form.get('payment_method', '')
            expense.payment_status = request.form.get('payment_status', 'PAID')
            expense.vendor = request.form.get('vendor', '')
            expense.invoice_number = request.form.get('invoice_number', '')
            expense.receipt_number = request.form.get('receipt_number', '')
            expense.is_recurring = request.form.get('is_recurring') == 'on'
            expense.recurring_frequency = request.form.get('recurring_frequency', '')
            
            # Update next due date for recurring expenses
            if expense.is_recurring and expense.recurring_frequency:
                if expense.recurring_frequency == 'MONTHLY':
                    expense.next_due_date = expense.expense_date + timedelta(days=30)
                elif expense.recurring_frequency == 'QUARTERLY':
                    expense.next_due_date = expense.expense_date + timedelta(days=90)
                elif expense.recurring_frequency == 'YEARLY':
                    expense.next_due_date = expense.expense_date + timedelta(days=365)
            
            db.session.commit()
            flash(f'Expense {expense.expense_id} updated successfully!', 'success')
            return redirect(url_for('expenses.list_expenses'))
            
        except Exception as e:
            flash(f'Error updating expense: {str(e)}', 'error')
            db.session.rollback()
    
    categories = ExpenseCategory.query.filter(ExpenseCategory.is_active == True).all()
    return render_template('expenses/form.html', expense=expense, categories=categories)

@expenses_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_expense(id):
    """Delete expense"""
    expense = Expense.query.get_or_404(id)
    
    try:
        expense_id = expense.expense_id
        db.session.delete(expense)
        db.session.commit()
        flash(f'Expense {expense_id} deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting expense: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('expenses.list_expenses'))

@expenses_bp.route('/categories')
@login_required
def list_categories():
    """Manage expense categories"""
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return render_template('expenses/categories.html', categories=categories)

@expenses_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    """Add expense category"""
    try:
        # Create new category with proper attribute assignment
        category = ExpenseCategory()
        category.name = request.form['name']
        category.description = request.form.get('description', '')
        category.color = request.form.get('color', '#3B82F6')
        
        db.session.add(category)
        db.session.commit()
        flash(f'Category "{category.name}" added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding category: {str(e)}', 'error')
        db.session.rollback()
    
    return redirect(url_for('expenses.list_categories'))

@expenses_bp.route('/reports')
@login_required
def reports():
    """Expense and sales reports"""
    report_type = request.args.get('report_type', 'monthly')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    today = date.today()
    
    # Set default date range based on report type
    if not date_from or not date_to:
        if report_type == 'daily':
            date_from_obj = today
            date_to_obj = today
        elif report_type == 'weekly':
            # Last 7 days inclusive (today and 6 prior days)
            date_from_obj = today - timedelta(days=6)
            date_to_obj = today
        elif report_type == 'monthly':
            date_from_obj = today.replace(day=1)
            date_to_obj = today
        else:  # yearly
            date_from_obj = today.replace(month=1, day=1)
            date_to_obj = today
    else:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Generate report data
    report_data = generate_sales_report(date_from_obj, date_to_obj, report_type)
    
    return render_template('expenses/reports.html',
                         report_data=report_data,
                         report_type=report_type,
                         date_from=date_from_obj.isoformat(),
                         date_to=date_to_obj.isoformat())

def generate_sales_report(date_from, date_to, report_type):
    """Generate comprehensive sales and expense report"""
    # Define datetime range for completion timestamps (inclusive of end date)
    start_dt = datetime.combine(date_from, datetime.min.time())
    end_dt_exclusive = datetime.combine(date_to + timedelta(days=1), datetime.min.time())

    # Completed laundries within range via status history
    completed_subq = db.session.query(LaundryStatusHistory.laundry_id).filter(
        and_(
            LaundryStatusHistory.new_status == 'Completed',
            LaundryStatusHistory.changed_at >= start_dt,
            LaundryStatusHistory.changed_at < end_dt_exclusive
        )
    ).subquery()

    # Revenue from completed laundries in period
    total_revenue = db.session.query(func.sum(Laundry.price)).filter(
        Laundry.laundry_id.in_(completed_subq)
    ).scalar() or 0

    # Total laundries completed in period
    laundry_count = db.session.query(func.count(func.distinct(LaundryStatusHistory.laundry_id))).filter(
        and_(
            LaundryStatusHistory.new_status == 'Completed',
            LaundryStatusHistory.changed_at >= start_dt,
            LaundryStatusHistory.changed_at < end_dt_exclusive
        )
    ).scalar() or 0
    
    # Total expenses
    expense_query = db.session.query(func.sum(Expense.amount)).filter(
        and_(
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to
        )
    )
    total_expenses = expense_query.scalar() or 0
    
    # Expense by category
    expense_categories = db.session.query(
        ExpenseCategory.name,
        ExpenseCategory.color,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        and_(
            Expense.expense_date >= date_from,
            Expense.expense_date <= date_to
        )
    ).group_by(ExpenseCategory.name, ExpenseCategory.color).all()
    
    # Service performance for completed laundries in period
    service_performance = db.session.query(
        Laundry.service_id,
        func.count(Laundry.id).label('count'),
        func.sum(Laundry.price).label('revenue')
    ).filter(
        Laundry.laundry_id.in_(completed_subq)
    ).group_by(Laundry.service_id).all()

    # Build daily timeseries per service for the selected range
    # Prepare date labels (historical)
    day = date_from
    labels_hist = []
    while day <= date_to:
        labels_hist.append(day.isoformat())
        day += timedelta(days=1)

    # Query daily revenue grouped by date and service for completed laundries
    daily_rows = db.session.query(
        func.date(LaundryStatusHistory.changed_at).label('day'),
        Laundry.service_id,
        func.sum(Laundry.price).label('revenue')
    ).join(Laundry, Laundry.laundry_id == LaundryStatusHistory.laundry_id).filter(
        and_(
            LaundryStatusHistory.new_status == 'Completed',
            LaundryStatusHistory.changed_at >= start_dt,
            LaundryStatusHistory.changed_at < end_dt_exclusive
        )
    ).group_by('day', Laundry.service_id).all()

    # Map service_id to name
    service_map = {s.id: s.name for s in Service.query.all()}

    # Aggregate into dict: service_id -> {date_iso: revenue}
    from collections import defaultdict
    per_service_daily = defaultdict(dict)
    daily_total_map = defaultdict(float)
    for row in daily_rows:
        day_iso = row.day.isoformat() if hasattr(row.day, 'isoformat') else str(row.day)
        per_service_daily[row.service_id][day_iso] = float(row.revenue or 0)
        daily_total_map[day_iso] += float(row.revenue or 0)

    # Determine top 5 services by revenue in range
    top_services = sorted(
        [(sid, float(sum(vals.values()))) for sid, vals in per_service_daily.items()],
        key=lambda x: x[1], reverse=True
    )[:5]

    # Build datasets for top services
    color_palette = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
        '#14b8a6', '#f43f5e', '#22c55e', '#6366f1', '#fb923c'
    ]
    datasets = []
    for idx, (sid, _total) in enumerate(top_services):
        series = []
        values_map = per_service_daily.get(sid, {})
        for d in labels_hist:
            series.append(values_map.get(d, 0))
        datasets.append({
            'label': service_map.get(sid, f'Service {sid}' if sid else 'Unknown'),
            'data': series,
            'borderColor': color_palette[idx % len(color_palette)],
            'backgroundColor': color_palette[idx % len(color_palette)] + '33',
            'tension': 0.3,
            'fill': False
        })

    # Total revenue per day series
    total_hist = [float(daily_total_map.get(d, 0)) for d in labels_hist]

    # Forecast next 7 days for total revenue using simple linear regression on last N days
    def linear_regression_forecast(series, steps=7):
        n = len(series)
        if n == 0:
            return [0] * steps
        # Use last up to 14 days for regression
        window = min(14, n)
        y = series[-window:]
        x = list(range(window))
        # Compute slope and intercept
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xx = sum(i*i for i in x)
        sum_xy = sum(i*y[i] for i in range(window))
        denom = window * sum_xx - sum_x * sum_x
        if denom == 0:
            slope = 0
            intercept = y[-1] if y else 0
        else:
            slope = (window * sum_xy - sum_x * sum_y) / denom
            intercept = (sum_y - slope * sum_x) / window
        # Forecast forward continuously from last index
        start_idx = window
        return [max(0, intercept + slope * (start_idx + k)) for k in range(steps)]

    forecast_steps = 7
    forecast_vals = linear_regression_forecast(total_hist, steps=forecast_steps)

    # Extend labels with future dates
    labels_full = labels_hist[:]
    next_day = date_to + timedelta(days=1)
    for _ in range(forecast_steps):
        labels_full.append(next_day.isoformat())
        next_day += timedelta(days=1)

    # Build datasets including total and forecast
    datasets_full = datasets[:]
    # Add total historical line
    datasets_full.append({
        'label': 'Total Revenue',
        'data': total_hist + [None] * forecast_steps,
        'borderColor': '#111827',
        'backgroundColor': '#11182733',
        'tension': 0.35,
        'fill': False,
        'borderWidth': 2
    })
    # Add forecast line aligned to future dates
    datasets_full.append({
        'label': 'Forecast (Total)',
        'data': [None] * len(labels_hist) + forecast_vals,
        'borderColor': '#111827',
        'backgroundColor': '#11182733',
        'tension': 0.35,
        'fill': False,
        'borderDash': [6, 3]
    })
    
    # Customer metrics
    new_customers = Customer.query.filter(
        and_(
            Customer.date_created >= date_from,
            Customer.date_created <= date_to
        )
    ).count()
    
    # Current inventory value
    inventory_value = db.session.query(
        func.sum(InventoryItem.current_stock * InventoryItem.cost_per_unit)
    ).scalar() or 0
    
    return {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': total_revenue - total_expenses,
        'laundry_count': laundry_count,
        'expense_categories': expense_categories,
        'service_performance': service_performance,
        'new_customers': new_customers,
        'inventory_value': inventory_value,
        'date_range': f"{date_from} to {date_to}",
        'timeseries': {
            'labels': labels_full,
            'historical_labels': labels_hist,
            'datasets': datasets_full
        }
    }
