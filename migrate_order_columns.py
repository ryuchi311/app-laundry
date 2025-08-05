"""
Migration script to add new columns to Order table
"""
from app import create_app, db
from app.models import Order, Service

def migrate_order_table():
    """Add new columns to Order table"""
    
    app = create_app()
    with app.app_context():
        try:
            # Connect to the database
            connection = db.engine.connect()
            
            # Check if columns exist before adding them
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('order')]
            
            print(f"Existing columns in 'order' table: {columns}")
            
            # Add service_id column if it doesn't exist
            if 'service_id' not in columns:
                print("Adding service_id column...")
                connection.execute(db.text('ALTER TABLE "order" ADD COLUMN service_id INTEGER'))
                print("✅ Added service_id column")
            else:
                print("⚠️  service_id column already exists")
            
            # Add weight_kg column if it doesn't exist
            if 'weight_kg' not in columns:
                print("Adding weight_kg column...")
                connection.execute(db.text('ALTER TABLE "order" ADD COLUMN weight_kg FLOAT DEFAULT 0.0'))
                print("✅ Added weight_kg column")
            else:
                print("⚠️  weight_kg column already exists")
            
            connection.commit()
            connection.close()
            
            # Now create the foreign key constraint (if needed)
            # Note: SQLite doesn't support adding foreign key constraints to existing tables
            # We'll handle this in the application logic instead
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_order_table()
