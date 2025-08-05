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

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(10), unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    item_count = db.Column(db.Integer)
    service_type = db.Column(db.String(50))  # Wash/Dry/Fold/Iron
    price = db.Column(db.Float, default=0.0)  # Total price for the order
    status = db.Column(db.String(20))  # Received, In Process, Ready for Pickup, Completed
    notes = db.Column(db.Text)  # Description of clothes/items
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Security tracking fields
    last_edited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    last_edited_at = db.Column(db.DateTime)
    edit_count = db.Column(db.Integer, default=0)
    is_modified = db.Column(db.Boolean, default=False)
    
    # Pricing system - flat rate per order
    PRICING = {
        'Wash Only': 150,      # ₱150 per order
        'Dry Only': 120,       # ₱120 per order
        'Wash & Dry': 200,     # ₱200 per order
        'Wash & Fold': 250,    # ₱250 per order
        'Full Service': 300,   # ₱300 per order (Wash, Dry, Fold, Iron)
        'Iron Only': 100,      # ₱100 per order
    }
    
    def calculate_price(self):
        """Calculate the total price based on service type (flat rate per order)"""
        if self.service_type:
            return self.PRICING.get(self.service_type, 200)  # Default ₱200 if service not found
        return 0.0
    
    def update_price(self):
        """Update the price field with calculated price"""
        self.price = self.calculate_price()

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
