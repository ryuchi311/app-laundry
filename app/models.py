from . import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='employee')  # 'super_admin', 'admin', 'manager', 'employee'
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def is_admin(self):
        """Check if user is admin or super admin"""
        return self.role in ['admin', 'super_admin']
    
    def is_manager(self):
        """Check if user is manager or higher"""
        return self.role in ['manager', 'admin', 'super_admin']
    
    def is_employee(self):
        """Check if user is employee (basic access)"""
        return self.role == 'employee'
    
    def is_super_admin(self):
        """Check if user is super admin"""
        return self.role == 'super_admin'
    
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role == 'super_admin'
    
    def can_manage_system(self):
        """Check if user can manage system settings"""
        return self.role in ['admin', 'super_admin']
    
    def can_view_reports(self):
        """Check if user can view financial reports"""
        return self.role in ['manager', 'admin', 'super_admin']
    
    def can_manage_inventory(self):
        """Check if user can manage inventory"""
        return self.role in ['manager', 'admin', 'super_admin']
    
    def can_manage_customers(self):
        """Check if user can add/edit customers"""
        return self.role in ['employee', 'manager', 'admin', 'super_admin']
    
    def can_process_laundry(self):
        """Check if user can process laundry orders"""
        return self.role in ['employee', 'manager', 'admin', 'super_admin']
    
    def can_view_all_orders(self):
        """Check if user can view all laundry orders"""
        return self.role in ['manager', 'admin', 'super_admin']
    
    def get_role_display(self):
        """Get human-readable role name"""
        role_names = {
            'super_admin': 'Super Administrator',
            'admin': 'Administrator',
            'manager': 'Manager',
            'employee': 'Employee'
        }
        return role_names.get(self.role, 'Employee')

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    laundries = db.relationship('Laundry', backref='customer', lazy=True)
    
    def get_loyalty_info(self):
        """Get customer's loyalty information"""
        from . import db
        loyalty = CustomerLoyalty.query.filter_by(customer_id=self.id).first()
        if not loyalty:
            # Create loyalty record if it doesn't exist
            loyalty = CustomerLoyalty()
            loyalty.customer_id = self.id
            db.session.add(loyalty)
            db.session.commit()
        return loyalty
    
    def is_regular_customer(self):
        """Check if customer is considered regular (5+ orders or Silver+ tier)"""
        loyalty = self.get_loyalty_info()
        return loyalty.total_orders >= 5 or loyalty.current_tier in ['Silver', 'Gold', 'Platinum']

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    base_price = db.Column(db.Float, nullable=False)
    price_per_kg = db.Column(db.Float, default=0.0)  # Optional per-kg pricing
    is_active = db.Column(db.Boolean, default=True)
    icon = db.Column(db.String(50), default='fas fa-tshirt')  # FontAwesome icon
    category = db.Column(db.String(50), default='Standard')  # Standard, Premium, Express
    estimated_hours = db.Column(db.Integer, default=24)  # Estimated completion time
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_total_price(self, item_count=1, weight_kg=0):
        """Calculate total price based on item count and optional weight"""
        base_total = self.base_price
        weight_total = self.price_per_kg * weight_kg if weight_kg > 0 else 0
        return base_total + weight_total
    
    def __repr__(self):
        return f'<Service {self.name}>'

class Laundry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    laundry_id = db.Column(db.String(10), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)  # New foreign key
    item_count = db.Column(db.Integer)
    service_type = db.Column(db.String(50))  # Keep for backward compatibility
    weight_kg = db.Column(db.Float, default=0.0)  # Optional weight for advanced pricing
    price = db.Column(db.Float, default=0.0)  # Total price for the laundry
    status = db.Column(db.String(20))  # Received, In Process, Ready for Pickup, Completed
    notes = db.Column(db.Text)  # Description of clothes/items
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service = db.relationship('Service', backref='laundries', lazy=True)
    
    # Security tracking fields
    last_edited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_edited_at = db.Column(db.DateTime)
    edit_count = db.Column(db.Integer, default=0)
    is_modified = db.Column(db.Boolean, default=False)
    
    # Legacy pricing system (for backward compatibility)
    PRICING = {
        'Wash Only': 150,      # ₱150 per laundry
        'Dry Only': 120,       # ₱120 per laundry
        'Wash & Dry': 200,     # ₱200 per laundry
        'Wash & Fold': 250,    # ₱250 per laundry
        'Full Service': 300,   # ₱300 per laundry (Wash, Dry, Fold, Iron)
        'Iron Only': 100,      # ₱100 per laundry
    }
    
    def calculate_price(self):
        """Calculate the total price based on service"""
        if self.service:
            # Use new service model pricing
            return self.service.calculate_total_price(self.item_count, self.weight_kg)
        # If relationship not loaded yet but service_id exists (e.g., before session flush)
        if self.service_id:
            try:
                service = Service.query.get(self.service_id)
                if service:
                    return service.calculate_total_price(self.item_count, self.weight_kg)
            except Exception:
                # Fallback below
                pass
        elif self.service_type:
            # Fall back to legacy pricing
            return self.PRICING.get(self.service_type, 200)
        return 0.0
    
    def update_price(self):
        """Update the price field with calculated price"""
        self.price = self.calculate_price()
    
    def get_service_name(self):
        """Get service name from either new service model or legacy service_type"""
        if self.service:
            return self.service.name
        return self.service_type or 'Unknown Service'
    
    def get_service_icon(self):
        """Get service icon"""
        if self.service:
            return self.service.icon
        return 'fas fa-tshirt'  # Default icon

class LaundryAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    laundry_id = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(20))  # CREATED, EDITED, STATUS_CHANGED
    field_changed = db.Column(db.String(50))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # For additional security tracking

class LaundryStatusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    laundry_id = db.Column(db.String(10), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationship to User
    changed_by_user = db.relationship('User', backref='status_changes')
    
    @staticmethod
    def log_status_change(laundry_id, old_status, new_status, changed_by, notes=None):
        """Log a status change"""
        if old_status != new_status:  # Only log if status actually changed
            history = LaundryStatusHistory()
            history.laundry_id = laundry_id
            history.old_status = old_status
            history.new_status = new_status
            history.changed_by = changed_by
            history.notes = notes
            
            db.session.add(history)
            return history
        return None
    
    def get_time_since_change(self):
        """Get human-readable time since this status change"""
        now = datetime.utcnow()
        diff = now - self.changed_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

class InventoryCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-box')
    color = db.Column(db.String(20), default='blue')  # For UI color coding
    is_active = db.Column(db.Boolean, default=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    items = db.relationship('InventoryItem', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name: str, description: str | None = None, icon: str = 'fas fa-box', color: str = 'blue', is_active: bool = True):
        self.name = name
        self.description = description
        self.icon = icon
        self.color = color
        self.is_active = is_active
    
    def __repr__(self):
        return f'<InventoryCategory {self.name}>'

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('inventory_category.id'), nullable=False)
    
    # Stock Information
    current_stock = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=10)  # Reorder level
    maximum_stock = db.Column(db.Integer, default=100)  # Maximum capacity
    unit_of_measure = db.Column(db.String(20), default='pieces')  # pieces, liters, kg, bottles, etc.
    
    # Pricing Information
    cost_per_unit = db.Column(db.Float, default=0.0)
    selling_price = db.Column(db.Float, default=0.0)
    
    # Item Details
    brand = db.Column(db.String(100))
    model_number = db.Column(db.String(100))
    supplier = db.Column(db.String(150))
    barcode = db.Column(db.String(100), unique=True)
    image_filename = db.Column(db.String(255))  # Store uploaded image filename
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_consumable = db.Column(db.Boolean, default=True)  # True for supplies, False for equipment
    
    # Tracking
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    stock_movements = db.relationship('StockMovement', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, name: str, category_id: int, description: str | None = None, 
                 current_stock: int = 0, minimum_stock: int = 10, maximum_stock: int = 100,
                 unit_of_measure: str = 'pieces', cost_per_unit: float = 0.0, 
                 selling_price: float = 0.0, brand: str | None = None, 
                 model_number: str | None = None, supplier: str | None = None,
                 barcode: str | None = None, image_filename: str | None = None,
                 is_active: bool = True, is_consumable: bool = True, created_by: int | None = None):
        self.name = name
        self.category_id = category_id
        self.description = description
        self.current_stock = current_stock
        self.minimum_stock = minimum_stock
        self.maximum_stock = maximum_stock
        self.unit_of_measure = unit_of_measure
        self.cost_per_unit = cost_per_unit
        self.selling_price = selling_price
        self.brand = brand
        self.model_number = model_number
        self.supplier = supplier
        self.barcode = barcode
        self.image_filename = image_filename
        self.is_active = is_active
        self.is_consumable = is_consumable
        self.created_by = created_by
    
    @property
    def stock_status(self):
        """Return stock status based on current stock levels"""
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.current_stock <= self.minimum_stock:
            return 'low_stock'
        elif self.current_stock >= self.maximum_stock:
            return 'overstock'
        else:
            return 'normal'
    
    @property
    def stock_value(self):
        """Calculate total value of current stock"""
        return self.current_stock * self.cost_per_unit
    
    def needs_reorder(self):
        """Check if item needs to be reordered"""
        return self.current_stock <= self.minimum_stock
    
    def __repr__(self):
        return f'<InventoryItem {self.name}>'

class StockMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    
    # Movement Details
    movement_type = db.Column(db.String(20), nullable=False)  # 'IN', 'OUT', 'ADJUSTMENT', 'TRANSFER'
    quantity = db.Column(db.Integer, nullable=False)  # Positive for IN, negative for OUT
    unit_cost = db.Column(db.Float, default=0.0)
    
    # Stock levels before and after
    stock_before = db.Column(db.Integer, nullable=False)
    stock_after = db.Column(db.Integer, nullable=False)
    
    # Reference Information
    reference_type = db.Column(db.String(50))  # 'PURCHASE', 'USAGE', 'ADJUSTMENT', 'RETURN'
    reference_id = db.Column(db.String(100))  # Invoice number, laundry ID, etc.
    notes = db.Column(db.Text)
    
    # Tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    created_by_user = db.relationship('User', backref='stock_movements')
    
    @staticmethod
    def create_movement(item_id, movement_type, quantity, created_by, reference_type=None, reference_id=None, notes=None, unit_cost=0.0):
        """Create a stock movement and update item stock"""
        from . import db
        
        item = InventoryItem.query.get(item_id)
        if not item:
            return None
            
        stock_before = item.current_stock
        
        # Calculate new stock level
        if movement_type in ['IN', 'PURCHASE', 'RETURN']:
            stock_after = stock_before + abs(quantity)
        elif movement_type in ['OUT', 'USAGE', 'CONSUMPTION']:
            stock_after = max(0, stock_before - abs(quantity))
        else:  # ADJUSTMENT
            stock_after = quantity  # Direct set for adjustments
            
        # Create movement record
        movement = StockMovement()
        movement.item_id = item_id
        movement.movement_type = movement_type
        movement.quantity = quantity
        movement.unit_cost = unit_cost
        movement.stock_before = stock_before
        movement.stock_after = stock_after
        movement.reference_type = reference_type
        movement.reference_id = reference_id
        movement.notes = notes
        movement.created_by = created_by
        
        # Update item stock
        item.current_stock = stock_after
        item.date_updated = datetime.utcnow()
        
        db.session.add(movement)
        return movement
    
    def __repr__(self):
        return f'<StockMovement {self.movement_type} {self.quantity} for Item {self.item_id}>'

class ExpenseCategory(db.Model):
    """Categories for business expenses"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color for UI
    is_active = db.Column(db.Boolean, default=True)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'

class Expense(db.Model):
    """Business expense tracking"""
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.String(20), unique=True, nullable=False)  # EXP-001, EXP-002, etc.
    
    # Basic Information
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_category.id'), nullable=False)
    
    # Date Information
    expense_date = db.Column(db.Date, nullable=False)  # When the expense occurred
    due_date = db.Column(db.Date)  # For recurring bills
    
    # Classification
    expense_type = db.Column(db.String(20), default='ONE_TIME')  # ONE_TIME, RECURRING, MAINTENANCE
    payment_method = db.Column(db.String(50))  # CASH, BANK_TRANSFER, CHECK, CREDIT_CARD
    payment_status = db.Column(db.String(20), default='PAID')  # PAID, PENDING, OVERDUE
    
    # Reference Information
    vendor = db.Column(db.String(200))  # Who was paid
    invoice_number = db.Column(db.String(100))
    receipt_number = db.Column(db.String(100))
    
    # Recurring Information
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_frequency = db.Column(db.String(20))  # MONTHLY, QUARTERLY, YEARLY
    next_due_date = db.Column(db.Date)
    
    # Tracking
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def generate_expense_id(self):
        """Generate unique expense ID"""
        if not self.expense_id:
            # Get the highest expense number
            last_expense = Expense.query.order_by(Expense.id.desc()).first()
            if last_expense and last_expense.expense_id:
                try:
                    last_num = int(last_expense.expense_id.split('-')[1])
                    new_num = last_num + 1
                except:
                    new_num = 1
            else:
                new_num = 1
            self.expense_id = f"EXP-{new_num:03d}"
    
    def __repr__(self):
        return f'<Expense {self.expense_id}: {self.title}>'

class SalesReport(db.Model):
    """Daily/Monthly sales summary"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Period Information
    report_date = db.Column(db.Date, nullable=False)
    report_type = db.Column(db.String(20), default='DAILY')  # DAILY, WEEKLY, MONTHLY, YEARLY
    
    # Sales Metrics
    total_laundries = db.Column(db.Integer, default=0)
    total_revenue = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    net_profit = db.Column(db.Float, default=0.0)
    
    # Inventory Metrics
    inventory_value = db.Column(db.Float, default=0.0)
    inventory_purchases = db.Column(db.Float, default=0.0)
    inventory_usage = db.Column(db.Float, default=0.0)
    
    # Customer Metrics
    new_customers = db.Column(db.Integer, default=0)
    returning_customers = db.Column(db.Integer, default=0)
    
    # Service Breakdown (JSON field for flexibility)
    service_breakdown = db.Column(db.Text)  # JSON string of service performance
    expense_breakdown = db.Column(db.Text)  # JSON string of expense categories
    
    # Tracking
    generated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SalesReport {self.report_date} - {self.report_type}>'

class LoyaltyProgram(db.Model):
    """Loyalty program configuration"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Program Settings
    name = db.Column(db.String(100), default="ACCIO Rewards")
    points_per_peso = db.Column(db.Float, default=1.0)  # Points earned per peso spent
    peso_per_point = db.Column(db.Float, default=0.10)  # Peso value per point when redeeming
    min_spend_for_points = db.Column(db.Float, default=50.0)  # Minimum spend to earn points
    min_points_to_redeem = db.Column(db.Integer, default=100)  # Minimum points to redeem
    
    # Tier Settings
    bronze_threshold = db.Column(db.Integer, default=0)     # 0 points
    silver_threshold = db.Column(db.Integer, default=500)   # 500 points  
    gold_threshold = db.Column(db.Integer, default=1500)    # 1500 points
    platinum_threshold = db.Column(db.Integer, default=3000) # 3000 points
    
    # Tier Multipliers
    bronze_multiplier = db.Column(db.Float, default=1.0)    # 1x points
    silver_multiplier = db.Column(db.Float, default=1.2)    # 1.2x points
    gold_multiplier = db.Column(db.Float, default=1.5)      # 1.5x points
    platinum_multiplier = db.Column(db.Float, default=2.0)  # 2x points
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_tier_info(self, total_points):
        """Get customer tier info based on points"""
        if total_points >= self.platinum_threshold:
            return 'Platinum', self.platinum_multiplier, 'fas fa-gem', 'text-purple-600'
        elif total_points >= self.gold_threshold:
            return 'Gold', self.gold_multiplier, 'fas fa-crown', 'text-yellow-600'
        elif total_points >= self.silver_threshold:
            return 'Silver', self.silver_multiplier, 'fas fa-medal', 'text-gray-500'
        else:
            return 'Bronze', self.bronze_multiplier, 'fas fa-award', 'text-orange-600'
    
    def __repr__(self):
        return f'<LoyaltyProgram {self.name}>'

class CustomerLoyalty(db.Model):
    """Customer loyalty points and tier tracking"""
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False, unique=True)
    
    # Points Balance
    total_points_earned = db.Column(db.Integer, default=0)
    total_points_redeemed = db.Column(db.Integer, default=0)
    current_points = db.Column(db.Integer, default=0)  # earned - redeemed
    
    # Tier Information
    current_tier = db.Column(db.String(20), default='Bronze')
    tier_start_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Statistics
    total_orders = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Float, default=0.0)
    last_order_date = db.Column(db.DateTime)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='loyalty', lazy=True)
    point_transactions = db.relationship('LoyaltyTransaction', backref='customer_loyalty', lazy=True)
    
    def update_tier(self, loyalty_program):
        """Update customer tier based on total points earned"""
        tier, multiplier, icon, color = loyalty_program.get_tier_info(self.total_points_earned)
        if tier != self.current_tier:
            self.current_tier = tier
            self.tier_start_date = datetime.utcnow()
        return tier, multiplier, icon, color
    
    def can_redeem(self, points_to_redeem, loyalty_program):
        """Check if customer can redeem specified points"""
        return (self.current_points >= points_to_redeem and 
                points_to_redeem >= loyalty_program.min_points_to_redeem)
    
    def __repr__(self):
        return f'<CustomerLoyalty Customer: {self.customer_id} - {self.current_tier}>'

class LoyaltyTransaction(db.Model):
    """Individual loyalty point transactions"""
    id = db.Column(db.Integer, primary_key=True)
    customer_loyalty_id = db.Column(db.Integer, db.ForeignKey('customer_loyalty.id'), nullable=False)
    
    # Transaction Details
    transaction_type = db.Column(db.String(20), nullable=False)  # 'EARNED', 'REDEEMED', 'EXPIRED', 'BONUS'
    points = db.Column(db.Integer, nullable=False)  # Positive for earned, negative for redeemed
    description = db.Column(db.String(200))
    
    # Related Records
    laundry_id = db.Column(db.Integer, db.ForeignKey('laundry.id'), nullable=True)  # If earned from order
    order_amount = db.Column(db.Float, nullable=True)  # Order amount that generated points
    redemption_value = db.Column(db.Float, nullable=True)  # Peso value when redeeming
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User who processed
    
    # Relationships
    laundry = db.relationship('Laundry', backref='loyalty_transactions', lazy=True)
    
    def __repr__(self):
        return f'<LoyaltyTransaction {self.transaction_type}: {self.points} points>'

class SMSSettings(db.Model):
    """SMS notification settings and custom messages"""
    id = db.Column(db.Integer, primary_key=True)
    
    # SMS Status Settings
    received_enabled = db.Column(db.Boolean, default=True)
    in_process_enabled = db.Column(db.Boolean, default=True)
    ready_pickup_enabled = db.Column(db.Boolean, default=True)
    completed_enabled = db.Column(db.Boolean, default=True)
    welcome_enabled = db.Column(db.Boolean, default=True)
    
    # Custom SMS Message Templates (with placeholders)
    received_message = db.Column(db.Text, default="Hi {customer_name}! Your laundry (#{laundry_id}) has been received and is being processed. - {sender_name}")
    in_process_message = db.Column(db.Text, default="Hi {customer_name}! Your laundry (#{laundry_id}) is now being processed. We'll notify you when it's ready! - {sender_name}")
    ready_pickup_message = db.Column(db.Text, default="Hi {customer_name}! Great news! Your laundry (#{laundry_id}) is ready for pickup. Please visit us during business hours. - {sender_name}")
    completed_message = db.Column(db.Text, default="Hi {customer_name}! Your laundry (#{laundry_id}) has been completed. Thank you for choosing {sender_name}!")
    welcome_message = db.Column(db.Text, default="Welcome to {sender_name}, {customer_name}! We're excited to serve you. For inquiries, contact us at +639761111464.")
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    @staticmethod
    def get_settings():
        """Get the SMS settings (creates default if none exists)"""
        settings = SMSSettings.query.first()
        if not settings:
            settings = SMSSettings()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def format_message(
        self,
        message_template: str,
        customer_name: str,
        laundry_id: str,
        sender_name: str = "ACCIO Laundry",
        number_of_items: "int|str|None" = None,
    ) -> str:
        """Format message template with actual values, supporting both {number_of_items} and {Number of Items}.
        Note: {Number of Items} (with spaces) is replaced before .format() to avoid KeyError.
        """
        # Normalize number_of_items to string
        noi = "" if number_of_items is None else str(number_of_items)

        # Pre-replace the non-identifier placeholder with spaces
        msg = message_template.replace("{Number of Items}", noi)

        # Also support snake_case placeholder via .format
        return msg.format(
            customer_name=customer_name,
            laundry_id=laundry_id,
            sender_name=sender_name,
            number_of_items=noi,
        )
    
    def __repr__(self):
        return f'<SMSSettings ID: {self.id}>'

class SMSSettingsProfile(db.Model):
    """Named profiles for SMS settings"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    is_default = db.Column(db.Boolean, default=False)

    # Settings fields (same as SMSSettings)
    received_enabled = db.Column(db.Boolean, default=True)
    in_process_enabled = db.Column(db.Boolean, default=True)
    ready_pickup_enabled = db.Column(db.Boolean, default=True)
    completed_enabled = db.Column(db.Boolean, default=True)
    welcome_enabled = db.Column(db.Boolean, default=True)

    received_message = db.Column(db.Text, default="Hi {customer_name}! Your laundry (#{laundry_id}) has been received and is being processed. - {sender_name}")
    in_process_message = db.Column(db.Text, default="Hi {customer_name}! Your laundry (#{laundry_id}) is now being processed. We'll notify you when it's ready! - {sender_name}")
    ready_pickup_message = db.Column(db.Text, default="Hi {customer_name}! Great news! Your laundry (#{laundry_id}) is ready for pickup. Please visit us during business hours. - {sender_name}")
    completed_message = db.Column(db.Text, default="Hi {customer_name}! Your laundry (#{laundry_id}) has been completed. Thank you for choosing {sender_name}!")
    welcome_message = db.Column(db.Text, default="Welcome to {sender_name}, {customer_name}! We're excited to serve you. For inquiries, contact us at +639761111464.")

    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def apply_to_active(self):
        """Copy this profile's settings into the active SMSSettings singleton"""
        settings = SMSSettings.get_settings()
        settings.received_enabled = self.received_enabled
        settings.in_process_enabled = self.in_process_enabled
        settings.ready_pickup_enabled = self.ready_pickup_enabled
        settings.completed_enabled = self.completed_enabled
        settings.welcome_enabled = self.welcome_enabled
        settings.received_message = self.received_message
        settings.in_process_message = self.in_process_message
        settings.ready_pickup_message = self.ready_pickup_message
        settings.completed_message = self.completed_message
        settings.welcome_message = self.welcome_message
        return settings

    def set_as_default(self):
        """Mark this profile as default and unset others"""
        for p in SMSSettingsProfile.query.all():
            p.is_default = (p.id == self.id)
        return self

    @staticmethod
    def create_from_active(name: str, user_id: int | None = None, make_default: bool = False):
        s = SMSSettings.get_settings()
        profile = SMSSettingsProfile()
        profile.name = (name or '').strip() or 'Profile'
        profile.is_default = bool(make_default)
        profile.received_enabled = s.received_enabled
        profile.in_process_enabled = s.in_process_enabled
        profile.ready_pickup_enabled = s.ready_pickup_enabled
        profile.completed_enabled = s.completed_enabled
        profile.welcome_enabled = s.welcome_enabled
        profile.received_message = s.received_message
        profile.in_process_message = s.in_process_message
        profile.ready_pickup_message = s.ready_pickup_message
        profile.completed_message = s.completed_message
        profile.welcome_message = s.welcome_message
        profile.updated_by = user_id
        db.session.add(profile)
        # Ensure only one default
        if make_default:
            for p in SMSSettingsProfile.query.all():
                if p is not profile:
                    p.is_default = False
        return profile

    def format_message(
        self,
        message_template: str,
        customer_name: str,
        laundry_id: str,
        sender_name: str = "ACCIO Laundry",
        number_of_items: "int|str|None" = None,
    ) -> str:
        """Same formatter as SMSSettings for convenience when used directly"""
        noi = "" if number_of_items is None else str(number_of_items)
        msg = message_template.replace("{Number of Items}", noi)
        return msg.format(
            customer_name=customer_name,
            laundry_id=laundry_id,
            sender_name=sender_name,
            number_of_items=noi,
        )

    def __repr__(self):
        return f"<SMSSettingsProfile {self.name} ({'default' if self.is_default else 'custom'})>"

class BulkMessageHistory(db.Model):
    """Track sent bulk messages for audit and history"""
    id = db.Column(db.Integer, primary_key=True)
    message_text = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)  # promo, event, announcement
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_recipients = db.Column(db.Integer, default=0)
    successful_sends = db.Column(db.Integer, default=0)
    failed_sends = db.Column(db.Integer, default=0)
    
    # Relationships
    sent_by = db.relationship('User', backref='bulk_messages_sent')
    
    def get_success_rate(self):
        """Calculate success rate percentage"""
        if self.total_recipients == 0:
            return 0
        return round((self.successful_sends / self.total_recipients) * 100, 1)
    
    def get_time_since_sent(self):
        """Get human-readable time since message was sent"""
        if not self.sent_at:
            return "Not sent yet"
            
        now = datetime.utcnow()
        diff = now - self.sent_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"
    
    def __repr__(self):
        return f'<BulkMessage {self.message_type}: {self.total_recipients} recipients>'


class Notification(db.Model):
    """User notifications for system events"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime)
    
    # Optional reference to related objects
    related_model = db.Column(db.String(50))  # laundry, customer, expense, etc.
    related_id = db.Column(db.String(50))     # ID of the related object
    
    # Action URL (optional)
    action_url = db.Column(db.String(500))
    action_text = db.Column(db.String(100))
    
    def __init__(self, user_id=None, title=None, message=None, notification_type='info',
                 related_model=None, related_id=None, action_url=None, action_text=None, **kwargs):
        """Initialize notification with explicit parameters"""
        super().__init__(**kwargs)
        if user_id is not None:
            self.user_id = user_id
        if title is not None:
            self.title = title
        if message is not None:
            self.message = message
        if notification_type is not None:
            self.notification_type = notification_type
        if related_model is not None:
            self.related_model = related_model
        if related_id is not None:
            self.related_id = related_id
        if action_url is not None:
            self.action_url = action_url
        if action_text is not None:
            self.action_text = action_text
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def get_time_ago(self):
        """Get human-readable time since notification was created"""
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    
    def __repr__(self):
        return f'<Notification {self.title}: {self.notification_type}>'


class DashboardWidget(db.Model):
    """Model for storing user dashboard widget preferences"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    widget_id = db.Column(db.String(50), nullable=False)  # e.g., 'stats_overview', 'recent_orders'
    position = db.Column(db.Integer, default=0)  # Order position
    is_visible = db.Column(db.Boolean, default=True)
    grid_column = db.Column(db.Integer, default=1)  # Grid column (1-3)
    grid_row = db.Column(db.Integer, default=1)  # Grid row
    widget_size = db.Column(db.String(20), default='normal')  # 'small', 'normal', 'large'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='dashboard_widgets')
    
    def __init__(self, user_id: int, widget_id: str, position: int = 0, 
                 is_visible: bool = True, grid_column: int = 1, grid_row: int = 1, 
                 widget_size: str = 'normal'):
        self.user_id = user_id
        self.widget_id = widget_id
        self.position = position
        self.is_visible = is_visible
        self.grid_column = grid_column
        self.grid_row = grid_row
        self.widget_size = widget_size
    
    def __repr__(self):
        return f'<DashboardWidget {self.widget_id} for user {self.user_id}>'

class BusinessSettings(db.Model):
    """Business information and branding settings"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Business Information
    business_name = db.Column(db.String(200), default='ACCIO')
    business_tagline = db.Column(db.String(200), default='Labhonon Laundry')
    business_description = db.Column(db.Text, default='Professional laundry services with quality care')
    
    # Contact Information
    phone = db.Column(db.String(50), default='+639761111464')
    email = db.Column(db.String(150), default='info@acciolaundry.com')
    address = db.Column(db.Text, default='Purok 17, Lower Mandacpan, Brgy. San Vicente, Butuan City, Philippines')
    
    # Operating Hours
    operating_hours = db.Column(db.Text, default='Monday - Sunday: 6:00 AM - 8:00 PM')
    
    # Footer Information
    footer_text = db.Column(db.Text, default='Quality laundry services you can trust')
    copyright_text = db.Column(db.String(200), default='© 2025 ACCIO Labhonon Laundry. All rights reserved.')
    
    # Social Media (optional)
    facebook_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    website_url = db.Column(db.String(255))
    
    # System Settings
    currency_symbol = db.Column(db.String(10), default='₱')
    date_format = db.Column(db.String(20), default='%B %d, %Y')
    timezone = db.Column(db.String(50), default='Asia/Manila')
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationship
    updated_by_user = db.relationship('User', backref='business_settings_updates')
    
    @staticmethod
    def get_settings():
        """Get business settings (creates default if none exists)"""
        settings = BusinessSettings.query.first()
        if not settings:
            settings = BusinessSettings()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<BusinessSettings {self.business_name}>'
