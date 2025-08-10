# Business Settings Management - Super Admin Feature

## Overview
Created a comprehensive business settings management system that allows Super Admins to customize business information, branding, contact details, and footer content throughout the entire application.

## Features
- **Super Admin Only Access**: Restricted to users with Super Admin privileges
- **Dynamic Branding**: Changes apply globally across all pages
- **Live Preview**: Preview changes before saving
- **Comprehensive Settings**: Business info, contact details, social media, system settings
- **Context-Aware Updates**: All templates automatically use updated settings

## Settings Categories

### 🏢 **Business Information**
- **Business Name**: Main company/brand name (replaces "ACCIO")
- **Business Tagline**: Subtitle/tagline (replaces "Labhonon Laundry") 
- **Business Description**: Detailed description of services

### 📞 **Contact Information**
- **Phone Number**: Primary contact number
- **Email Address**: Business email
- **Business Address**: Full address with location details
- **Operating Hours**: Business hours display

### 🎨 **Footer & Branding**
- **Footer Text**: Main footer message
- **Copyright Text**: Copyright notice with year
- **Custom Branding**: Consistent across all pages

### 📱 **Social Media (Optional)**
- **Facebook URL**: Link to Facebook page
- **Instagram URL**: Link to Instagram profile
- **Website URL**: Link to main website

### ⚙️ **System Settings**
- **Currency Symbol**: Default currency (₱, $, €, etc.)
- **Timezone**: System timezone selection

## Technical Implementation

### Database Model
```python
class BusinessSettings(db.Model):
    # Business Information
    business_name = db.Column(db.String(200), default='ACCIO')
    business_tagline = db.Column(db.String(200), default='Labhonon Laundry')
    business_description = db.Column(db.Text)
    
    # Contact Information
    phone, email, address, operating_hours
    
    # Footer & Branding
    footer_text, copyright_text
    
    # Social Media Links
    facebook_url, instagram_url, website_url
    
    # System Settings
    currency_symbol, timezone
```

### Global Context Processor
```python
@app.context_processor
def inject_business_settings():
    return dict(business_settings=BusinessSettings.get_settings())
```

### Security & Access Control
- **Super Admin Decorator**: `@super_admin_required`
- **Authentication Required**: `@login_required`
- **Role Verification**: `current_user.is_super_admin()`

## User Interface Features

### 🎨 **Modern Design**
- **Gradient Headers**: Color-coded sections
- **Card-based Layout**: Organized information blocks
- **Responsive Design**: Works on all device sizes
- **Professional Icons**: FontAwesome icons throughout

### 📱 **Interactive Elements**
- **Live Preview**: See changes before saving
- **Form Validation**: Required field validation
- **Success Notifications**: Confirmation messages
- **Loading States**: User feedback during operations

### 🔍 **Preview System**
- **Modal Preview**: Popup showing how changes will look
- **Header Preview**: Shows updated business name/tagline
- **Footer Preview**: Shows updated footer content
- **Contact Preview**: Shows updated contact information

## Global Impact

### Updated Throughout Application
1. **Page Titles**: `{{ business_settings.business_name }} {{ business_settings.business_tagline }}`
2. **Navigation Header**: Dynamic business name and tagline
3. **Footer Information**: Dynamic address, phone, email, copyright
4. **Contact Displays**: Consistent contact information

### Affected Templates
- **base.html**: Header, footer, page titles
- **All extending templates**: Inherit updated branding
- **Contact pages**: Use dynamic contact info
- **Footer sections**: Use dynamic footer text

## Files Created/Modified

### New Files
1. **`app/business_settings.py`** - Blueprint with routes and logic
2. **`app/templates/business_settings.html`** - Settings interface

### Modified Files
1. **`app/models.py`** - Added BusinessSettings model
2. **`app/__init__.py`** - Blueprint registration, context processor
3. **`app/templates/base.html`** - Dynamic content integration

## Navigation Integration
- **Features Dropdown**: Added "Business Settings" menu item
- **Super Admin Only**: Visible only to Super Admin users
- **Professional Icon**: Building icon for easy recognition

## Use Cases
- **Rebranding**: Change business name and tagline across entire app
- **Contact Updates**: Update phone, email, address globally
- **Footer Management**: Customize footer content and copyright
- **Multi-tenant Support**: Different branding for different installations

## Default Values
- **Business Name**: "ACCIO"
- **Business Tagline**: "Labhonon Laundry"
- **Phone**: "+639761111464"
- **Address**: "Purok 17, Lower Mandacpan, Brgy. San Vicente, Butuan City, Philippines"
- **Currency**: "₱"
- **Timezone**: "Asia/Manila"

## Future Enhancements
- **Logo Upload**: Custom logo support
- **Color Themes**: Customizable color schemes
- **Multi-language**: Language selection
- **Advanced Branding**: Custom CSS injection
- **Email Templates**: Branded email templates

## Date: August 10, 2025
## Status: ✅ Implemented with Global Context Integration
