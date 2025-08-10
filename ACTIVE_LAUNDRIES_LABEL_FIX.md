# Dashboard Label Fix - "Today's Activity" to "Active Laundries"

## Issue Fixed
Changed misleading label from "Today's Activity" to "Active Laundries" to accurately reflect the data being displayed.

## Problem
- **Misleading Label**: The section was labeled "Today's Activity" but was showing all-time active laundries
- **Data Mismatch**: The backend query counts ALL laundries with status != 'Completed', regardless of date
- **User Confusion**: Users expected to see today's specific activity, not cumulative active orders

## Solution Applied
**Option 2**: Changed the label to match the existing backend logic rather than changing the logic.

### Backend Logic (Unchanged)
```python
active_laundries = Laundry.query.filter(Laundry.status != 'Completed').count()
```

This counts all laundry orders that are currently active (not completed), including:
- Status: "Received"
- Status: "In Process" 
- Status: "Ready for Pickup"
- Any other status except "Completed"

### Frontend Change
**Before:**
```html
<p class="text-sm text-gray-600">Today's Activity</p>
<p class="text-lg font-bold text-gray-900">{{ active_laundries }} active</p>
```

**After:**
```html
<p class="text-sm text-gray-600">Active Laundries</p>
<p class="text-lg font-bold text-gray-900">{{ active_laundries }} active</p>
```

## Benefits
1. **Accurate Labeling**: The label now correctly describes what the data represents
2. **Clear Understanding**: Users immediately understand this shows all currently active orders
3. **No Backend Changes**: Maintained existing functionality while improving clarity
4. **Consistent UX**: Users get the information they expect based on the label

## Alternative Options Considered
- **Option 1**: Change backend to show true today's activity (more complex, requires date filtering)
- **Option 3**: Show today's new orders (different metric entirely)

## Files Modified
- `app/templates/dashboard.html`: Updated label from "Today's Activity" to "Active Laundries"

## User Impact
- ✅ More accurate understanding of the metric
- ✅ No confusion about time period
- ✅ Clear indication of current workload/active orders
- ✅ Maintains existing business logic

## Date: August 10, 2025
## Status: ✅ Fixed and Accurate
