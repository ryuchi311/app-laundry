# Earned Today Card - AttributeError Fix

## Issue Resolved
Fixed the `AttributeError: type object 'Laundry' has no attribute 'date_completed'` that was preventing the dashboard from loading.

## Problem
The dashboard was trying to calculate today's earnings using a non-existent field `date_completed` in the Laundry model. The Laundry model only has `date_received` and `date_updated` fields.

## Solution
Changed the today's earnings calculation to use `date_updated` instead of `date_completed`. This makes logical sense because when a laundry's status is changed to 'Completed', the `date_updated` field gets updated to reflect when the status change occurred.

## Changes Made
**File: `app/views.py`**
```python
# Before (caused error)
today_earnings = db.session.query(func.sum(Laundry.price)).filter(
    Laundry.status == 'Completed',
    func.date(Laundry.date_completed) == today
).scalar() or 0

# After (fixed)
today_earnings = db.session.query(func.sum(Laundry.price)).filter(
    Laundry.status == 'Completed',
    func.date(Laundry.date_updated) == today
).scalar() or 0
```

## Result
- Dashboard now loads without errors
- "Earned Today" card displays correctly for all user roles
- Application functions normally

## Date: August 10, 2025
## Status: ✅ Fixed and Working
