# Multi-Load Laundry Feature - Quick Start Guide

## ✨ What's New?

You can now add **multiple laundry loads for one customer** in a single form submission! Perfect for customers bringing multiple loads with different services.

## 🚀 Quick Access

1. **Dashboard** → Click "Multi-Load" in Quick Actions
2. **Laundry List** → Click "Multi-Load" button in the header
3. **Single Load Form** → Click "Multi-Load" button to switch

## 📝 How It Works

### Step 1: Select Customer
Search and select the customer (same as before)

### Step 2: Add Loads
- Form starts with 1 load
- Click **"Add Load"** to add more (up to 20)
- Each load has:
  - ✅ Service Type (Wash Only, Wash & Dry, etc.)
  - ✅ Number of Items
  - ✅ Weight (kg)
  - ✅ Optional Notes

### Step 3: Review & Submit
- See live summary: Total Loads, Total Weight, Total Price
- Click **"Create All Loads"** to submit

## 💡 Example Use Case

**Customer brings 3 separate loads:**

| Load | Service | Items | Weight | Price |
|------|---------|-------|--------|-------|
| #1 | Wash & Dry | 10 | 8 kg | ₱200 |
| #2 | Full Service | 15 | 10 kg | ₱300 |
| #3 | Wash Only | 5 | 5 kg | ₱150 |

**Result:** 3 separate laundry entries created instantly with unique IDs!

## ✨ Features

- ✅ Real-time price calculation per load
- ✅ Live total summary
- ✅ Remove any load with trash icon
- ✅ Each load tracked independently
- ✅ All loads get SMS/email notifications
- ✅ Full audit trail for each load

## 🎯 Benefits

1. **Save Time** - No need to fill the form multiple times
2. **Less Errors** - Customer selected once
3. **Better Tracking** - All loads from same visit created together
4. **Flexible** - Different services for each load

## 🔧 Technical Info

- **URL**: `/laundry/add-multiple`
- **Backend**: `app/laundry.py` → `add_multiple_laundry()`
- **Frontend**: `templates/laundries/laundry_add_multiple.html`
- **Status**: Each load starts as "Received"

## 📋 Files Modified

1. ✅ `app/laundry.py` - Added new route and handler
2. ✅ `app/templates/laundries/laundry_add_multiple.html` - New multi-load form
3. ✅ `app/templates/laundries/laundry_list.html` - Added "Multi-Load" button
4. ✅ `app/templates/laundries/laundry_add.html` - Added "Multi-Load" link
5. ✅ `app/templates/dashboard.html` - Added "Multi-Load" quick action

## 🎨 UI Features

- **Beautiful gradient header** with layer icon
- **Dynamic load cards** with smooth animations
- **Real-time pricing** updates as you type
- **Summary dashboard** showing totals
- **Responsive design** works on all devices
- **Professional styling** matching your app's theme

## 🔒 Security & Validation

- ✅ Login required
- ✅ Customer validation
- ✅ Service validation
- ✅ Weight minimum: 0.1 kg
- ✅ At least 1 load required
- ✅ All loads validated before submission

## 📱 Try It Now!

1. Go to your laundry app
2. Click **"Multi-Load"** on the dashboard
3. Select a customer
4. Add a few test loads with different services
5. Submit and see all loads created!

---

**Enjoy the new multi-load feature! 🎉**
