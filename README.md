# ACCIO Labhonon Laundry Services

A modern, comprehensive web-based laundry management system built with Flask and TailwindCSS, featuring dynamic service management, real-time pricing calculations, and a professional user interface.

## Features

### 🔐 Authentication & User Management
- Secure user registration and login
- Profile settings with password change functionality
- User session management with Flask-Login
- Email validation and security features

### 👥 Customer Management
- Complete CRUD operations for customer data
- Customer contact information tracking
- Order history per customer
- Search and filter capabilities

### 📦 Advanced Order Management
- Dynamic order creation with real-time pricing
- Weight-based and service-based pricing calculations
- Order status tracking and updates
- Unique order ID generation
- Order history and analytics

### 🎯 Dynamic Service Management
- Configurable service types and categories
- Real-time pricing with base price + per-kg calculations
- Premium service tiers with gold styling
- Service icons and estimated completion times
- Active/inactive service toggles

### 📊 Analytics Dashboard
- Real-time business metrics and KPIs
- Dynamic pricing cards with service information
- Order statistics and revenue tracking
- Visual charts and data visualization
- Service performance analytics

### 📧 Communication
- Automated email notifications
- Order confirmation emails
- Status update notifications
- Customer communication tracking

### 🎨 Modern UI/UX
- Responsive design with TailwindCSS
- Professional color schemes and typography
- FontAwesome icons throughout
- Mobile-first responsive design
- Intuitive navigation and user experience
- Gold styling for premium services with crown icons

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (for cloning the repository)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ryuchi311/app-laundry.git
cd app-laundry
```

2. **Create a virtual environment:**
```bash
python -m venv .venv
```

3. **Activate the virtual environment:**
```bash
# Windows
.venv\Scripts\activate

# Unix/MacOS
source .venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set up environment variables:**
Create a `.env` file in the root directory:
```env
FLASK_APP=main.py
FLASK_DEBUG=1
SECRET_KEY=your-super-secret-key-change-this-in-production
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

6. **Initialize the database:**
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

7. **Run database migrations (if available):**
```bash
# Run any pending migrations in the migrations/ folder
python -c "
import sqlite3
conn = sqlite3.connect('instance/laundry.db')
# Any migration scripts would go here
conn.close()
"
```

8. **Start the application:**
```bash
python main.py
```

The application will be available at `http://localhost:5000`

### Default Login
After setting up, you can create an admin account through the registration page or use the application interface to manage your laundry business.

## 📁 Project Structure

```
app-laundry/
├── app/
│   ├── __init__.py              # Flask app factory and configuration
│   ├── models.py                # Database models (User, Customer, Order, Service)
│   ├── auth.py                  # Authentication routes and logic
│   ├── views.py                 # Main dashboard and analytics
│   ├── customer.py              # Customer management CRUD
│   ├── order.py                 # Order management and processing
│   ├── service.py               # Service management and pricing
│   ├── profile.py               # User profile and settings
│   ├── static/
│   │   ├── css/                 # Custom stylesheets
│   │   ├── js/                  # JavaScript for interactivity
│   │   └── images/              # Static assets
│   └── templates/
│       ├── base.html            # Base template with navigation
│       ├── dashboard.html       # Analytics dashboard
│       ├── auth/                # Authentication templates
│       ├── customers/           # Customer management templates
│       ├── orders/              # Order management templates
│       ├── services/            # Service management templates
│       └── profile/             # Profile settings templates
├── instance/
│   └── laundry.db              # SQLite database file
├── migrations/                  # Database migration scripts
├── .env                        # Environment variables (create this)
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── main.py                     # Application entry point
└── README.md                   # This file
```

## 🛠️ Technologies Used

- **Backend:** Flask (Python web framework)
- **Database:** SQLite with SQLAlchemy ORM
- **Authentication:** Flask-Login
- **Email:** Flask-Mail
- **Frontend:** HTML5, TailwindCSS, JavaScript
- **Icons:** FontAwesome
- **Deployment:** Can be deployed on Heroku, PythonAnywhere, or any WSGI server

## 🎯 Key Components

### Models
- **User:** Authentication and profile management
- **Customer:** Client information and contact details
- **Service:** Dynamic pricing and service configuration
- **Order:** Complete order lifecycle management

### Blueprints
- **views:** Dashboard and analytics
- **auth:** Login, registration, logout
- **customer:** Customer CRUD operations
- **order:** Order management workflow
- **service:** Service configuration and pricing
- **profile:** User settings and preferences

## 💡 Features in Detail

### Dynamic Pricing System
- Base pricing per service
- Additional per-kilogram pricing
- Real-time price calculations
- Service category management (Standard, Premium, Express)

### Premium Service Styling
- Gold color scheme for premium services
- Crown icons for luxury services
- Enhanced visual hierarchy
- Professional appearance

### Dashboard Analytics
- Revenue tracking
- Order statistics
- Service performance metrics
- Dynamic pricing display cards

### Responsive Design
- Mobile-first approach
- TailwindCSS utility classes
- Cross-device compatibility
- Modern UI components

## 🔧 Configuration

### Email Setup
To enable email notifications, configure your email provider in the `.env` file:

**For Gmail:**
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in the `.env` file

**For other providers:**
Update the `MAIL_SERVER` and `MAIL_PORT` in `app/__init__.py`

### Database Configuration
The application uses SQLite by default. For production, consider:
- PostgreSQL for better performance
- MySQL for compatibility
- Update the `SQLALCHEMY_DATABASE_URI` in the configuration

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment
1. Set `FLASK_DEBUG=False` in production
2. Use a production WSGI server like Gunicorn
3. Configure a reverse proxy (Nginx)
4. Use environment variables for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏢 Business Information

**ACCIO Labhonon Laundry Services**

📍 **Address:**
Purok 17, Lower Mandacpan,
Brgy. San Vicente,
Butuan City, Philippines

📞 **Phone:** +639761111464

📧 **Email:** Contact through the application

---

### 🌟 About This System

This laundry management system was designed to modernize and streamline laundry business operations. It provides a complete solution for managing customers, services, orders, and pricing with a professional, user-friendly interface.

**Key Benefits:**
- Reduce manual paperwork
- Improve customer experience
- Track business performance
- Automate pricing calculations
- Professional business image

For support or questions about the system, please contact the development team or create an issue in the repository.
