# ACCIO Labhonon Laundry Services

A comprehensive web-based laundry management system built with Flask and TailwindCSS.

## Features

- User Authentication
- Customer Management (CRUD)
- Order Management
- Email Notifications
- Dashboard with Analytics
- Responsive Design

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows: `.venv\Scripts\activate`
- Unix/MacOS: `source .venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following:
```
FLASK_APP=main.py
FLASK_DEBUG=1
SECRET_KEY=your-secret-key
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-email-password
```

5. Initialize the database:
```bash
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
```

6. Run the application:
```bash
flask run
```

## Project Structure

```
app-laundry/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── auth.py
│   ├── views.py
│   ├── customer.py
│   ├── order.py
│   ├── static/
│   └── templates/
├── .env
├── requirements.txt
└── main.py
```

## Contact Information

Purok 17, Lower Mandacpan,
Brgy. San Vicente,
Butuan City, Philippines


