# ACCIO Laundry Management System

## Overview
ACCIO is a modern laundry business management system built with Python and Flask. It provides user management, business analytics, customer tracking, financials, inventory, and live weather integration for your business location.

## Features
- Role-based access: Super Admin, Admin, Manager, User
- Dashboard with business KPIs and quick actions
- Customer management and statistics
- Financials and sales tracking
- Inventory management
- Loyalty program
- Expense tracking
- SMS notifications
- Live weather card (powered by WeatherAPI)
- Responsive UI with Tailwind CSS

## Getting Started
1. **Clone the repository**
   ```bash
   git clone https://github.com/ryuchi311/app-laundry.git
   cd app-laundry
   ```
2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   - Create a `.env` file for secrets (see `.env.example`)
   - Add your WeatherAPI key, email credentials, etc.
4. **Run the app**
   ```bash
   python main.py
   ```

## Configuration
- **WeatherAPI**: Set your API key in `.env` as `WEATHER_API_KEY`
- **Business Address**: Update in the admin panel or directly in the database

## Folder Structure
- `app/` - Main application code
- `app/templates/` - Jinja2 HTML templates
- `app/static/` - Static assets (CSS, JS, images)
- `instance/` - SQLite database
- `scripts/` - Utility scripts for data and user management

## License
MIT

## Author
ryuchi311
