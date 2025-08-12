"""
Migration script to add Stock Inventory Management tables
"""

import sqlite3
from datetime import datetime

def migrate():
    """Add inventory management tables to the database"""
    try:
        # Connect to database
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()
        
        # Check if inventory tables already exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory_category'")
        if cursor.fetchone():
            print("Inventory tables already exist. Migration may have already been run.")
            conn.close()
            return
        
        print("Starting migration: Adding Inventory Management tables...")
        
        # Create InventoryCategory table
        cursor.execute('''
            CREATE TABLE inventory_category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                icon VARCHAR(50) DEFAULT 'fas fa-box',
                color VARCHAR(20) DEFAULT 'blue',
                is_active BOOLEAN DEFAULT 1,
                date_created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ Created InventoryCategory table")
        
        # Create InventoryItem table
        cursor.execute('''
            CREATE TABLE inventory_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(150) NOT NULL,
                description TEXT,
                category_id INTEGER NOT NULL,
                current_stock INTEGER DEFAULT 0,
                minimum_stock INTEGER DEFAULT 10,
                maximum_stock INTEGER DEFAULT 100,
                unit_of_measure VARCHAR(20) DEFAULT 'pieces',
                cost_per_unit FLOAT DEFAULT 0.0,
                selling_price FLOAT DEFAULT 0.0,
                brand VARCHAR(100),
                model_number VARCHAR(100),
                supplier VARCHAR(150),
                barcode VARCHAR(100) UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                is_consumable BOOLEAN DEFAULT 1,
                date_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                date_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (category_id) REFERENCES inventory_category (id),
                FOREIGN KEY (created_by) REFERENCES user (id)
            )
        ''')
        print("✓ Created InventoryItem table")
        
        # Create StockMovement table
        cursor.execute('''
            CREATE TABLE stock_movement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                movement_type VARCHAR(20) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_cost FLOAT DEFAULT 0.0,
                stock_before INTEGER NOT NULL,
                stock_after INTEGER NOT NULL,
                reference_type VARCHAR(50),
                reference_id VARCHAR(100),
                notes TEXT,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES inventory_item (id),
                FOREIGN KEY (created_by) REFERENCES user (id)
            )
        ''')
        print("✓ Created StockMovement table")
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX idx_inventory_item_category ON inventory_item(category_id)')
        cursor.execute('CREATE INDEX idx_inventory_item_barcode ON inventory_item(barcode)')
        cursor.execute('CREATE INDEX idx_stock_movement_item ON stock_movement(item_id)')
        cursor.execute('CREATE INDEX idx_stock_movement_created_at ON stock_movement(created_at)')
        print("✓ Created performance indexes")
        
        # Insert default categories
        default_categories = [
            ('Detergents & Soaps', 'Laundry detergents, fabric softeners, and cleaning soaps', 'fas fa-bottle-water', 'blue'),
            ('Cleaning Supplies', 'General cleaning supplies and chemicals', 'fas fa-spray-can', 'green'),
            ('Equipment & Tools', 'Washing machines, dryers, and maintenance tools', 'fas fa-tools', 'orange'),
            ('Packaging Materials', 'Bags, hangers, tags, and packaging supplies', 'fas fa-shopping-bag', 'purple'),
            ('Office Supplies', 'Paper, pens, forms, and administrative materials', 'fas fa-paperclip', 'gray'),
            ('Maintenance', 'Parts, lubricants, and maintenance supplies', 'fas fa-wrench', 'red')
        ]
        
        cursor.executemany('''
            INSERT INTO inventory_category (name, description, icon, color, is_active, date_created)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
        ''', default_categories)
        print(f"✓ Added {len(default_categories)} default categories")
        
        # Insert sample inventory items
        sample_items = [
            ('Liquid Laundry Detergent', 'Heavy-duty liquid detergent for commercial use', 1, 5, 2, 50, 'liters', 25.0, 0.0, 'Tide', 'TD-5L', 'Wholesale Supplies Co.', None, 1, 1),
            ('Fabric Softener', 'Commercial grade fabric softener', 1, 8, 3, 30, 'liters', 18.0, 0.0, 'Downy', 'DW-4L', 'Wholesale Supplies Co.', None, 1, 1),
            ('Bleach', 'Chlorine bleach for whitening and disinfection', 2, 3, 1, 20, 'liters', 12.0, 0.0, 'Clorox', 'CX-2L', 'Chemical Supply Inc.', None, 1, 1),
            ('Plastic Garment Bags', 'Clear plastic bags for clean clothes', 4, 150, 50, 1000, 'pieces', 0.15, 0.0, 'ClearBag', 'CB-100', 'Packaging Pro', None, 1, 1),
            ('Wire Hangers', 'Metal wire hangers for hanging clothes', 4, 80, 20, 500, 'pieces', 0.25, 0.0, 'HangIt', 'HI-WH', 'Supplies Direct', None, 1, 1)
        ]
        
        cursor.executemany('''
            INSERT INTO inventory_item (name, description, category_id, current_stock, minimum_stock, maximum_stock, 
                                      unit_of_measure, cost_per_unit, selling_price, brand, model_number, supplier, 
                                      barcode, is_active, is_consumable, date_created, date_updated, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        ''', sample_items)
        print(f"✓ Added {len(sample_items)} sample inventory items")
        
        # Create initial stock movements for sample items
        stock_movements = [
            (1, 'IN', 5, 25.0, 0, 5, 'INITIAL', 'SETUP', 'Initial stock setup', 1),
            (2, 'IN', 8, 18.0, 0, 8, 'INITIAL', 'SETUP', 'Initial stock setup', 1),
            (3, 'IN', 3, 12.0, 0, 3, 'INITIAL', 'SETUP', 'Initial stock setup', 1),
            (4, 'IN', 150, 0.15, 0, 150, 'INITIAL', 'SETUP', 'Initial stock setup', 1),
            (5, 'IN', 80, 0.25, 0, 80, 'INITIAL', 'SETUP', 'Initial stock setup', 1)
        ]
        
        cursor.executemany('''
            INSERT INTO stock_movement (item_id, movement_type, quantity, unit_cost, stock_before, stock_after,
                                      reference_type, reference_id, notes, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', stock_movements)
        print(f"✓ Added {len(stock_movements)} initial stock movements")
        
        # Commit changes
        conn.commit()
        print("✓ Migration completed successfully")
        
        # Display summary
        print("\n=== Migration Summary ===")
        print("  - Added InventoryCategory table with default categories")
        print("  - Added InventoryItem table with sample items")
        print("  - Added StockMovement table for tracking changes")
        print("  - Created performance indexes")
        print("  - Added sample inventory data")
        print("  - Stock Inventory Management is now ready!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== Stock Inventory Management Migration Script ===")
    print("This script will add inventory management tables and sample data.")
    
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() in ['y', 'yes']:
        migrate()
        print("\nMigration completed! You can now manage inventory in your laundry system.")
    else:
        print("Migration cancelled.")
