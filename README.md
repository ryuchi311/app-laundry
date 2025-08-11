# 🧺 Laundry Management System

A comprehensive web-based laundry management application built with Flask, featuring role-based access control, SMS marketing, and complete business management tools.

## 🚀 Features

### 👥 User Management & Authentication
- **Multi-Role System**: Super Admin, Admin, Manager, Employee roles
- **Role-Based Dashboard**: Customized interface for each user role
- **Secure Authentication**: Flask-Login with session management
- **User Status Control**: Enable/disable user accounts

### 🏢 Business Management
- **Dynamic Business Settings**: Customizable business name, tagline, and contact information
- **Dashboard Analytics**: Real-time business metrics and KPIs
- **Today's Earnings Tracker**: Live daily revenue monitoring
- **Status Indicators**: Online status and system health monitoring

### 👤 Customer Directory
- **Customer Management**: Add, edit, and manage customer information
- **No-Delete Policy**: Customers can only be enabled/disabled (data protection)
- **Status-Based Operations**: Visual indicators for active/inactive customers
- **Customer Search & Filtering**: Easy customer lookup and management

### 💼 Service Management
- **Service Catalog**: Comprehensive laundry service management
- **Pricing Control**: Flexible pricing for different service types
- **Service Analytics**: Popular services tracking and insights

### 📱 SMS Marketing System
- **Bulk SMS Campaigns**: Send marketing messages to customers
- **Active Customer Targeting**: Only active customers receive bulk messages
- **SMS Credit Tracking**: Monitor SMS service usage and costs
- **Campaign History**: Track and review past marketing campaigns

### 📊 Dashboard & Analytics
- **Role-Specific Views**: Different dashboard content based on user permissions
- **Real-Time Metrics**: Live business performance indicators
- **Notification System**: Dynamic message transitions and alerts
- **Financial Overview**: Revenue tracking and business insights

## 🛠️ Technical Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Authentication**: Flask-Login
- **SMS Service**: Semaphore API integration
- **File Upload**: Secure image handling

## 🏗️ Project Structure

```
app-laundry/
├── app/
│   ├── __init__.py              # App initialization and configuration
│   ├── models.py               # Database models
│   ├── views.py                # Main dashboard and core views
│   ├── auth.py                 # Authentication routes
│   ├── customer.py             # Customer management
│   ├── service.py              # Service management
│   ├── sms_settings.py         # SMS marketing functionality
│   ├── business_settings.py    # Business configuration
│   ├── sms_service.py          # SMS API integration
│   └── templates/              # Jinja2 templates
│       ├── base.html          # Base template
│       ├── dashboard.html     # Main dashboard
│       ├── customer_list.html # Customer directory
│       ├── bulk_message.html  # SMS marketing
│       └── ...
├── instance/
│   └── laundry.db             # SQLite database
├── static/                    # Static assets
├── migrations/                # Database migration scripts
└── README.md                 # This file
```

## 🔐 User Roles & Permissions

| Feature | Super Admin | Admin | Manager | Employee |
|---------|-------------|-------|---------|----------|
| **Dashboard Analytics** | ✅ Full Access | ✅ Full Access | ✅ Operational | ✅ Basic |
| **Customer Management** | ✅ Full CRUD | ✅ Full CRUD | ✅ View/Edit | ✅ View Only |
| **Service Management** | ✅ Full Control | ✅ Full Control | ✅ View/Edit | ❌ No Access |
| **SMS Marketing** | ✅ Full Access | ✅ Full Access | ✅ Send Only | ❌ No Access |
| **Business Settings** | ✅ Full Control | ❌ View Only | ❌ View Only | ❌ No Access |
| **User Management** | ✅ Full Control | ✅ Limited | ❌ No Access | ❌ No Access |
| **Financial Reports** | ✅ Full Access | ✅ Full Access | ✅ Limited | ❌ No Access |

## 📋 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd app-laundry
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up the database**
```bash
python setup_database.py
```

5. **Run the application**
```bash
python main.py
```

6. **Access the application**
- Open your browser to `http://127.0.0.1:5000`
- Login with the default admin account:
  - Email: `admin@laundry.com`
  - Password: `admin123`

## 👤 Default User Accounts

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Super Admin** | superadmin@laundry.com | admin123 | Full system access |
| **Admin** | admin@laundry.com | admin123 | Business operations |
| **Manager** | manager@laundry.com | manager123 | Daily operations |
| **Employee** | employee@laundry.com | employee123 | Basic operations |

## ⚙️ Configuration

### SMS Settings
1. Navigate to **SMS Settings** in the application
2. Configure your SMS service provider (Semaphore API)
3. Add your API key and sender information
4. Test the connection before sending bulk messages

### Business Settings (Super Admin Only)
1. Go to **Features** → **Business Settings**
2. Update business name, tagline, and contact information
3. Customize footer and social media links
4. Changes apply globally across the application

## 🚦 Key Features Breakdown

### Customer Management
- **Data Protection**: No customer deletion - only enable/disable
- **Status Filtering**: SMS marketing only targets active customers
- **Comprehensive Profiles**: Store customer contact and preference information

### SMS Marketing
- **Targeted Campaigns**: Automatically excludes inactive customers
- **Credit Management**: Track SMS usage and remaining credits
- **Campaign Analytics**: Monitor message delivery and engagement

### Dashboard Customization
- **Role-Based Widgets**: Different information displayed per user role
- **Real-Time Updates**: Live data refresh and notification system
- **Business Metrics**: Track daily earnings, active orders, and customer growth

## 🔧 Development

### Adding New Features
1. Create new routes in appropriate blueprint files
2. Add database models to `models.py`
3. Create templates in `app/templates/`
4. Update role permissions as needed

### Database Migrations
- Use the migration scripts in the `migrations/` folder
- Always backup database before running migrations
- Test migrations on development environment first

## 📞 Support & Documentation

### API Endpoints
- Authentication: `/auth/*`
- Customer API: `/customer/*`
- SMS API: `/sms-settings/*`
- Business API: `/business-settings/*`

### Troubleshooting
- Check Flask logs for error details
- Verify database permissions and file access
- Ensure SMS API credentials are correctly configured
- Test user permissions match expected role capabilities

## 🎯 Roadmap

- [ ] Advanced reporting and analytics
- [ ] Integration with payment gateways
- [ ] Mobile responsive improvements
- [ ] Automated backup system
- [ ] Multi-location support
- [ ] Inventory management integration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**🧺 Laundry Management System - Professional, Secure, and User-Friendly**
