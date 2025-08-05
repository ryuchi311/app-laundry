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
    orders = db.relationship('Order', backref='customer', lazy=True)

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

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(10), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)  # New foreign key
    item_count = db.Column(db.Integer)
    service_type = db.Column(db.String(50))  # Keep for backward compatibility
    weight_kg = db.Column(db.Float, default=0.0)  # Optional weight for advanced pricing
    price = db.Column(db.Float, default=0.0)  # Total price for the order
    status = db.Column(db.String(20))  # Received, In Process, Ready for Pickup, Completed
    notes = db.Column(db.Text)  # Description of clothes/items
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    service = db.relationship('Service', backref='orders', lazy=True)
    
    # Security tracking fields
    last_edited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_edited_at = db.Column(db.DateTime)
    edit_count = db.Column(db.Integer, default=0)
    is_modified = db.Column(db.Boolean, default=False)
    
    # Legacy pricing system (for backward compatibility)
    PRICING = {
        'Wash Only': 150,      # ₱150 per order
        'Dry Only': 120,       # ₱120 per order
        'Wash & Dry': 200,     # ₱200 per order
        'Wash & Fold': 250,    # ₱250 per order
        'Full Service': 300,   # ₱300 per order (Wash, Dry, Fold, Iron)
        'Iron Only': 100,      # ₱100 per order
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

class OrderAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(20))  # CREATED, EDITED, STATUS_CHANGED
    field_changed = db.Column(db.String(50))
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # For additional security tracking
