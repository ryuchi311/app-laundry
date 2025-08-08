from . import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
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
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_consumable = db.Column(db.Boolean, default=True)  # True for supplies, False for equipment
    
    # Tracking
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    stock_movements = db.relationship('StockMovement', backref='item', lazy=True, cascade='all, delete-orphan')
    
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
    
    def format_message(self, message_template: str, customer_name: str, laundry_id: str, sender_name: str = "ACCIO Laundry") -> str:
        """Format message template with actual values"""
        return message_template.format(
            customer_name=customer_name,
            laundry_id=laundry_id,
            sender_name=sender_name
        )
    
    def __repr__(self):
        return f'<SMSSettings ID: {self.id}>'
