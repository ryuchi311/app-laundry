# Multi-Load Laundry Feature

## Overview
The multi-load feature allows you to efficiently add multiple laundry loads for a single customer in one form submission. This is perfect for customers who bring multiple loads with different service types (e.g., three loads of 8kg each with different services).

## Key Features

### 1. **Single Customer, Multiple Loads**
- Select one customer and add as many loads as needed
- Each load can have:
  - Different service type (Wash Only, Wash & Dry, Full Service, etc.)
  - Different weight (in kg)
  - Different number of items
  - Individual notes/special instructions

### 2. **Dynamic Form**
- Start with one load form
- Click "Add Load" button to add more loads
- Remove any load with the trash icon
- Minimum: 1 load required
- Maximum: 20 loads supported

### 3. **Real-Time Pricing**
- Each load shows its calculated price instantly
- Summary section displays:
  - Total number of loads
  - Total combined weight (kg)
  - Total combined price (₱)

### 4. **Batch Processing**
- All loads are created together in one transaction
- Each load gets its own unique Laundry ID
- All loads receive notifications (SMS/Email)
- All loads are logged in the system

## How to Use

### Access Points
1. **Dashboard** → Quick Actions → "Multi-Load" button
2. **Laundry List** → "Multi-Load" button in header
3. **Single Load Form** → "Multi-Load" button in header

### Steps to Create Multiple Loads

1. **Select Customer**
   - Search by name, phone, or email
   - Customer selection is required and applies to all loads

2. **Fill Load Details**
   - For each load, specify:
     - Service Type (required)
     - Number of Items (required, minimum 1)
     - Weight in kg (required, minimum 0.1)
     - Notes (optional)
   
3. **Add More Loads**
   - Click "Add Load" button to add another load
   - Each new load appears with the same fields
   - Load numbers are shown as "Load #1", "Load #2", etc.

4. **Review Summary**
   - Check the total summary at the bottom
   - Verify total loads, weight, and price

5. **Submit**
   - Click "Create All Loads" button
   - All loads will be created simultaneously
   - Each load receives:
     - Unique Laundry ID
     - Status: "Received"
     - Audit logs
     - Customer notifications

## Example Use Case

**Scenario**: Customer brings three separate loads

**Load 1**
- Service: Wash & Dry
- Items: 10
- Weight: 8 kg
- Notes: White clothes only

**Load 2**
- Service: Full Service (Wash, Dry, Fold, Iron)
- Items: 15
- Weight: 10 kg
- Notes: Formal wear, handle with care

**Load 3**
- Service: Wash Only
- Items: 5
- Weight: 5 kg
- Notes: Delicate items, cold wash

**Result**: Three separate laundry entries are created with individual IDs, each trackable independently in the system.

## Benefits

1. **Time Savings** - Create multiple loads in one form instead of repeating the process
2. **Reduced Errors** - Customer selected once, reducing data entry mistakes
3. **Better Organization** - All loads from same visit are created together
4. **Flexibility** - Each load can have different service types and pricing
5. **Comprehensive Tracking** - Each load maintains its own lifecycle (status, pickup, etc.)

## Technical Details

### Database
- Each load is a separate `Laundry` record
- All loads share the same `customer_id`
- Each load has unique `laundry_id`
- Created in single database transaction

### Notifications
- Each load triggers its own notification
- SMS and email sent per load (if configured)
- All notifications indicate multi-load batch creation

### Audit Trail
- Each load gets creation audit log
- All logs include "(Multi-load batch)" notation
- Status history tracked per load

## Route Information

- **URL**: `/laundry/add-multiple`
- **Methods**: GET, POST
- **Access**: Login required
- **Template**: `laundries/laundry_add_multiple.html`
- **Function**: `add_multiple_laundry()` in `app/laundry.py`

## Form Field Names

For developers/debugging:
- Customer ID: `customerId`
- Service Type: `serviceType_1`, `serviceType_2`, etc.
- Item Count: `itemCount_1`, `itemCount_2`, etc.
- Weight: `weight_kg_1`, `weight_kg_2`, etc.
- Notes: `notes_1`, `notes_2`, etc.

## Future Enhancements (Potential)

- Template system: Save common multi-load patterns
- Quick copy: Duplicate load details
- Import from CSV/Excel
- Barcode scanning for rapid entry
- Customer presets based on history
