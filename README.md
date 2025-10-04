# 🧺 ACCIO Laundry Management System

## Overview
ACCIO is a comprehensive, modern laundry business management system built with Python and Flask. Designed for laundry shops of all sizes, it provides complete business management including customer tracking, real-time notifications, financial analytics, inventory control, loyalty rewards, and multi-channel communication.

## ✨ Key Features

### 🎯 Core Laundry Operations
- **Multi-Load Processing** - Create multiple laundry loads for one customer in a single transaction
- **Single Load Entry** - Quick entry for individual laundry orders
- **Service Management** - Flexible pricing with base rates and per-kg options
- **Status Tracking** - Real-time order status updates (Received, In Process, Ready for Pickup, Completed)
- **Receipt Generation** - Professional receipts with QR codes and customer details
- **Order History** - Complete audit trail with status change tracking

### 👥 Customer Management
- **Customer Database** - Comprehensive customer profiles with contact information
- **Customer Analytics** - Growth trends, retention cohorts, and spending patterns
- **Search & Filter** - Advanced search with server-side pagination for scalability
- **Loyalty Integration** - Automatic loyalty points tracking and tier progression

### 💰 Financial Management
- **Revenue Tracking** - Real-time sales monitoring and reporting
- **Expense Management** - Track operational costs with categorization
- **Financial Reports** - Daily, weekly, monthly financial summaries
- **Sales Analytics** - Interactive charts and business intelligence

### 📦 Inventory System
- **Stock Management** - Track detergents, supplies, and consumables
- **Low Stock Alerts** - Automated notifications for reorder points
- **Usage Tracking** - Monitor inventory consumption patterns
- **Dashboard Overview** - At-a-glance inventory status

### 🎁 Loyalty Program
- **Points System** - Configurable earn rates (points per peso spent)
- **Tier Management** - Bronze, Silver, Gold, Platinum tiers with thresholds
- **Point Redemption** - Convert points to discounts
- **Manual Awards** - Server-side searchable modal for awarding points
- **Bulk Awards** - Award points to all customers or by tier
- **Transaction History** - Complete audit trail of all point activities

### 📱 SMS Notifications
- **Automated Messages** - Status change notifications (Received, Ready, Completed)
- **Welcome Messages** - Greet new customers automatically
- **Bulk Messaging** - Marketing campaigns with recipient filtering
- **Message Templates** - Quick templates for common promotions
- **Profile System** - Save and switch between message configurations
- **Credit Monitoring** - Real-time SMS credit balance tracking
- **Customer Search** - Server-side searchable customer selector with Select/Deselect all

### 👤 User Management
- **Role-Based Access Control** - Super Admin, Admin, Manager, User roles
- **Permission System** - Granular permissions for sensitive operations
- **User Dashboard** - Personalized views based on role
- **Activity Tracking** - User action audit logs
- **Search with Button** - Enhanced user search with immediate filtering

### 📊 Analytics & Reporting
- **Real-time Dashboard** - KPIs, charts, and business metrics
- **Customer Analytics** - Cohort retention, lifetime value, growth trends
- **Interactive Charts** - Revenue, orders, and expense visualizations
- **Export Capabilities** - Download reports for external analysis

### 🔔 Notification System
- **Bell Icon with Badge** - Centered notification count display
- **Auto-Expanding Display** - Notification messages expand to available space
- **Real-time Updates** - WebSocket support for instant notifications
- **Notification History** - View and manage past notifications

### 🎨 User Experience
- **Modern UI** - Clean, professional interface with Tailwind CSS
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile
- **Search Enhancements** - Search boxes with buttons on all major pages
- **Professional Styling** - Consistent design language throughout
- **Accessibility** - ARIA labels, keyboard navigation, screen reader support

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) Docker for containerized deployment

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ryuchi311/app-laundry.git
   cd app-laundry
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory with the following:
   ```env
   # Flask Configuration
   SECRET_KEY=your-secret-key-here
   FLASK_ENV=development
   
   # Database (SQLite by default, or configure MySQL/PostgreSQL)
   DATABASE_URL=sqlite:///instance/laundry.db
   
   # SMS Configuration (Semaphore API)
   SEMAPHORE_API_KEY=your-semaphore-api-key
   SEMAPHORE_SENDER_NAME=YourBusiness
   
   # Email Configuration
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   
   # Weather API (Optional)
   WEATHER_API_KEY=your-weatherapi-key
   
   # Application Settings
   BUSINESS_NAME=ACCIO Laundry
   BUSINESS_ADDRESS=Your Business Address
   ```

4. **Initialize the database**
   ```bash
   python main.py
   # The database will be created automatically on first run
   ```

5. **Create initial super admin user**
   ```bash
   python scripts/create_superadmin_once.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```
   
   The application will be available at `http://localhost:5000`

### Default Credentials
After running the super admin script, use:
- **Username**: admin (or as configured in script)
- **Password**: (set during script execution)

## 📋 Configuration

### SMS Notifications
1. Sign up for [Semaphore](https://semaphore.co/) SMS service
2. Add your API key and sender name to `.env`
3. Configure message templates in SMS Settings dashboard
4. Enable/disable notifications per status type

### Loyalty Program
1. Navigate to Loyalty → Settings
2. Configure:
   - Points per peso spent
   - Points per peso discount
   - Tier thresholds (Bronze, Silver, Gold, Platinum)
3. Activate the program

### Services & Pricing
1. Go to Services menu
2. Add services with:
   - Base price (flat rate)
   - Price per kg (for weight-based pricing)
   - Estimated completion hours
3. Services can be activated/deactivated as needed

## 📁 Project Structure

```
app-laundry/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── auth.py                  # Authentication routes
│   ├── customer.py              # Customer management
│   ├── laundry.py               # Laundry operations (single & multi-load)
│   ├── expenses.py              # Expense tracking
│   ├── inventory.py             # Inventory management
│   ├── loyalty.py               # Loyalty program
│   ├── notifications.py         # Notification system
│   ├── sms_settings.py          # SMS configuration & bulk messaging
│   ├── service.py               # Service management
│   ├── user_management.py       # User & role management
│   ├── views.py                 # Main dashboard & analytics
│   ├── models.py                # SQLAlchemy database models
│   ├── sms_service.py           # SMS API integration
│   ├── decorators.py            # Authorization decorators
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── dashboard.html       # Main dashboard
│   │   ├── laundries/          # Laundry templates
│   │   ├── customer/           # Customer management
│   │   ├── loyalty/            # Loyalty program UI
│   │   ├── inventory/          # Inventory pages
│   │   ├── expenses/           # Expense tracking
│   │   ├── notifications/      # Notification center
│   │   └── ...
│   └── static/                  # CSS, JS, images
├── instance/
│   └── laundry.db              # SQLite database (default)
├── scripts/
│   ├── create_superadmin_once.py
│   ├── seed_customers.py
│   └── ...                      # Utility scripts
├── alembic/                     # Database migrations
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── main.py                      # Application entry point
└── README.md

```

## 🐳 Docker Deployment

### Local Docker Testing

Build and run the container locally (the app listens on port 8080):

```bash
# Build the image
docker build -t app-laundry:local .

# Run the container and expose port 8080
docker run --rm -p 8080:8080 \
  -e STARTUP_DEBUG=1 \
  -e SECRET_KEY=your-secret-key \
  -e SEMAPHORE_API_KEY=your-api-key \
  --name app-laundry-local \
  app-laundry:local

# In another terminal, check health endpoint:
curl -i http://localhost:8080/health
```

Set `STARTUP_DEBUG=1` to print additional startup diagnostics in container logs.

### Google Cloud Run Deployment

The application is optimized for Cloud Run deployment:

1. **Build and push to Google Container Registry**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/app-laundry
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy app-laundry \
     --image gcr.io/YOUR_PROJECT_ID/app-laundry \
     --platform managed \
     --region asia-southeast1 \
     --allow-unauthenticated \
     --set-env-vars="SECRET_KEY=your-secret-key,SEMAPHORE_API_KEY=your-api-key"
   ```

3. **Configure environment variables** in Cloud Run console or via command line

See `README_CLOUD_RUN.md` for detailed deployment instructions.

## 🔧 Development

### Database Migrations

Using Alembic for database schema changes:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_customer_analytics.py

# Run with coverage
python -m pytest --cov=app tests/
```

### Utility Scripts

Located in `scripts/` directory:

- `create_superadmin_once.py` - Create initial super admin user
- `seed_customers.py` - Add sample customer data
- `seed_tomorrow.py` - Generate test laundry orders
- `normalize_customer_phones.py` - Clean phone number formatting
- `update_user_role.py` - Change user roles
- `check_user_roles.py` - Verify user permissions

## 📚 API Endpoints

### Customer API
- `GET /api/customers` - Paginated customer list with search
  - Query params: `search`, `page`, `per_page`, `sort_by`, `sort_order`
  - Returns: JSON with customer data, pagination info

### Notifications API
- `GET /notifications/api/recent` - Recent notifications
- `GET /notifications/api/unread-count` - Unread notification count
- `POST /notifications/mark-read/<id>` - Mark notification as read

### SMS API
- `GET /sms-settings/customer-list` - Active customers with phone numbers
- `POST /sms-settings/compute-recipients` - Calculate bulk message recipients
- `POST /sms-settings/preview-bulk` - Preview formatted bulk message

## 🎨 UI/UX Features

### Search Enhancements
Search boxes with dedicated search buttons have been added to:
- Service List
- Expense List
- Inventory Items
- Inventory Dashboard (All Items link)
- Loyalty Customers
- User Management
- SMS Bulk Messaging (Customer selection)
- Loyalty Dashboard (Award Points modal)

All search interfaces support:
- Click search button to filter
- Press Enter to search
- Clear button to reset filter
- Server-side filtering for scalability

### Responsive Design
- Mobile-first approach
- Touch-friendly controls
- Adaptive layouts for all screen sizes
- Professional styling with Tailwind CSS

## 🔐 Security Features

- **Password Hashing** - Werkzeug bcrypt for secure password storage
- **Session Management** - Flask-Login for user sessions
- **CSRF Protection** - Built-in Flask CSRF tokens
- **Role-Based Access** - Decorator-based authorization
- **SQL Injection Prevention** - SQLAlchemy ORM parameterized queries
- **Environment Variables** - Sensitive data stored in `.env`

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Write docstrings for functions and classes

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**ryuchi311**
- GitHub: [@ryuchi311](https://github.com/ryuchi311)

## 🙏 Acknowledgments

- Flask framework and ecosystem
- Tailwind CSS for styling
- Semaphore for SMS services
- WeatherAPI for weather integration
- Font Awesome for icons
- All contributors and users

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation in the `/docs` folder
- Review feature documentation files (e.g., `MULTI_LOAD_FEATURE.md`)

## 🗺️ Roadmap

Future enhancements planned:
- [ ] Multi-language support (i18n)
- [ ] Mobile app (React Native)
- [ ] Advanced reporting with PDF export
- [ ] Integration with payment gateways
- [ ] Barcode/QR code scanning for pickup
- [ ] WhatsApp notifications
- [ ] Employee shift management
- [ ] Equipment maintenance tracking
- [ ] Customer feedback system
- [ ] Automated marketing campaigns

## 📊 System Requirements

**Minimum:**
- Python 3.8+
- 512 MB RAM
- 1 GB disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

**Recommended:**
- Python 3.10+
- 2 GB RAM
- 5 GB disk space
- PostgreSQL or MySQL for production

## 🌐 Browser Support

- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Mobile browsers (iOS Safari, Chrome Mobile)

---

**Built with ❤️ for laundry businesses worldwide**
