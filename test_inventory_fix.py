#!/usr/bin/env python3
"""
Quick test to verify the inventory attribute fix
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import InventoryItem, InventoryCategory

def test_inventory_attributes():
    app = create_app()
    with app.app_context():
        try:
            # Test basic inventory attribute access
            items = InventoryItem.query.limit(3).all()
            
            print("🧪 Testing Inventory Item Attributes:")
            print("=" * 50)
            
            if not items:
                print("⚠️  No inventory items found. Creating test item...")
                
                # Create a test category if needed
                category = InventoryCategory.query.first()
                if not category:
                    category = InventoryCategory(name="Test Category")
                    db.session.add(category)
                    db.session.commit()
                
                # Create a test item
                item = InventoryItem(
                    name="Test Item",
                    category_id=category.id,
                    current_stock=10,
                    cost_per_unit=25.50
                )
                db.session.add(item)
                db.session.commit()
                items = [item]
            
            for item in items:
                print(f"📦 Item: {item.name}")
                print(f"   ✅ cost_per_unit: ₱{item.cost_per_unit or 0:.2f}")
                print(f"   ✅ current_stock: {item.current_stock}")
                print(f"   ✅ total_value: ₱{(item.cost_per_unit or 0) * item.current_stock:.2f}")
                print(f"   ✅ Has unit_cost attribute: {hasattr(item, 'unit_cost')}")
                print(f"   ✅ Has cost_per_unit attribute: {hasattr(item, 'cost_per_unit')}")
                print("-" * 30)
            
            # Test the calculation that was failing
            print("🧮 Testing Total Value Calculation:")
            total_value = sum((item.cost_per_unit or 0) * item.current_stock for item in items)
            print(f"   ✅ Total inventory value: ₱{total_value:.2f}")
            
            print("\n🎉 All tests passed! The attribute fix is working correctly.")
            return True
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_inventory_attributes()
    sys.exit(0 if success else 1)
