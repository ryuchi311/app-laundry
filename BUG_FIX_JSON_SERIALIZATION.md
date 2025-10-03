# Multi-Load Feature - Bug Fix

## Issue
When accessing `/laundry/add-multiple`, the page threw a `TypeError`:
```
TypeError: Object of type Service is not JSON serializable
```

## Root Cause
The template was trying to serialize SQLAlchemy `Service` model objects directly to JSON using `{{ services | tojson }}`. SQLAlchemy model objects cannot be directly converted to JSON because they contain internal state and relationships.

## Solution
Created a JSON-serializable dictionary representation of the services before passing to the template.

### Changes Made

#### 1. `app/laundry.py` (lines ~341-357)
**Before:**
```python
services = Service.query.filter_by(is_active=True).all()
return render_template(
    "laundries/laundry_add_multiple.html",
    user=current_user,
    customers=customers,
    services=services,
)
```

**After:**
```python
services = Service.query.filter_by(is_active=True).all()

# Convert services to dictionary for JSON serialization
services_data = [
    {
        'id': s.id,
        'name': s.name,
        'base_price': float(s.base_price),
        'price_per_kg': float(s.price_per_kg),
        'estimated_hours': s.estimated_hours,
        'is_active': s.is_active
    }
    for s in services
]

return render_template(
    "laundries/laundry_add_multiple.html",
    user=current_user,
    customers=customers,
    services=services,           # For template loops
    services_json=services_data,  # For JavaScript JSON
)
```

#### 2. `app/templates/laundries/laundry_add_multiple.html` (line 240)
**Before:**
```javascript
let services = {{ services | tojson }};
```

**After:**
```javascript
let services = {{ services_json | tojson }};
```

## Result
✅ The page now loads successfully  
✅ Services are properly serialized to JavaScript  
✅ Multi-load form works as expected  

## Example JSON Output
The JavaScript receives clean, serializable data:
```json
[
  {
    "id": 1,
    "name": "Wash Only",
    "base_price": 150.0,
    "price_per_kg": 0.0,
    "estimated_hours": 6,
    "is_active": true
  },
  {
    "id": 2,
    "name": "Wash & Dry",
    "base_price": 200.0,
    "price_per_kg": 0.0,
    "estimated_hours": 8,
    "is_active": true
  }
]
```

## Testing
Verified with:
1. ✅ Service query works
2. ✅ JSON serialization succeeds
3. ✅ Route is registered: `/laundry/add-multiple`
4. ✅ No Python errors

The multi-load feature is now fully functional! 🎉
