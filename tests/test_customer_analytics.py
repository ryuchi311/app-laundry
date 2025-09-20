import os
import sys
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Customer, Laundry


@pytest.fixture
def app_instance(tmp_path_factory):
    db_fd = tmp_path_factory.mktemp('data') / 'test_analytics.db'
    # Ensure create_app picks up our test DB instead of any external DATABASE_URL
    os.environ['DATABASE_URL'] = f"sqlite:///{db_fd}"
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.app_context():
        db.create_all()
        # create admin user
        admin = User(email='admin@example.com', password='x', full_name='Admin', role='admin')
        db.session.add(admin)
        db.session.commit()
    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def login_client_as_admin(client, app_instance):
    with client.session_transaction() as sess:
        with app_instance.app_context():
            admin = User.query.filter_by(email='admin@example.com').first()
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True


def test_customer_analytics_no_customers(client, app_instance):
    login_client_as_admin(client, app_instance)
    resp = client.get('/customer-analytics')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Customer Analytics' in body
    # should show zero customers KPI
    assert 'Total Customers' in body


def test_customer_analytics_with_customers_and_laundries(client, app_instance):
    with app_instance.app_context():
        # create customers and laundries
        c1 = Customer(full_name='Alice')
        c2 = Customer(full_name='Bob')
        db.session.add_all([c1, c2])
        db.session.commit()
        # create laundries (completed)
        l1 = Laundry(customer_id=c1.id, price=200.0, status='Completed', date_received=datetime.utcnow())
        l2 = Laundry(customer_id=c2.id, price=150.0, status='Completed', date_received=datetime.utcnow())
        db.session.add_all([l1, l2])
        db.session.commit()

    login_client_as_admin(client, app_instance)
    resp = client.get('/customer-analytics')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Top Customers by Spend' in body
    assert 'Alice' in body or 'Bob' in body


def test_customer_analytics_date_filter_and_branch(client, app_instance):
    with app_instance.app_context():
        # create customer outside date range
        past = datetime.utcnow() - timedelta(days=200)
        c_old = Customer(full_name='Old')
        db.session.add(c_old)
        db.session.commit()
        l_old = Laundry(customer_id=c_old.id, price=50.0, status='Completed', date_received=past)
        db.session.add(l_old)
        db.session.commit()

    login_client_as_admin(client, app_instance)
    # apply recent date filter that should exclude the old customer
    resp = client.get('/customer-analytics?start=2025-01-01&end=2025-02-01')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Customer Growth' in body

