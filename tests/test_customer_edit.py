import os
import sys
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, Customer
from sqlalchemy.exc import IntegrityError


@pytest.fixture
def app_instance(tmp_path_factory):
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    db_fd = tmp_path_factory.mktemp('data') / 'test.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_fd}'
    with app.app_context():
        db.create_all()
        # create an admin user for testing or reuse existing
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User()
            admin.email = 'admin@example.com'
            admin.password = 'x'
            admin.full_name = 'Admin'
            admin.role = 'admin'
            db.session.add(admin)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
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


def test_edit_customer_happy_path(client, app_instance):
    with app_instance.app_context():
        # create customer
        c = Customer()
        c.full_name = 'Old Name'
        c.phone = '+639111111111'
        c.email = 'cust@example.com'
        db.session.add(c)
        db.session.commit()
        c_id = c.id

    login_client_as_admin(client, app_instance)

    # Post updated data
    resp = client.post(f'/customer/edit/{c_id}', data={
        'fullName': 'New Name',
        'phone': '+639122222222',
        'email': 'new@example.com',
        'is_active': 'on'
    }, follow_redirects=True)

    assert resp.status_code == 200
    with app_instance.app_context():
        updated = Customer.query.get(c_id)
        assert updated.full_name == 'New Name'
        assert updated.phone == '+639122222222'
        assert updated.email == 'new@example.com'
        assert updated.is_active is True


def test_edit_customer_invalid_phone_and_email(client, app_instance):
    with app_instance.app_context():
        c = Customer()
        c.full_name = 'User'
        c.phone = '+639111111111'
        c.email = 'u@example.com'
        db.session.add(c)
        db.session.commit()
        c_id = c.id

    login_client_as_admin(client, app_instance)

    # Invalid phone and email should not update and should flash errors (redirect back)
    resp = client.post(f'/customer/edit/{c_id}', data={
        'fullName': 'U',  # too short
        'phone': 'invalid-phone',
        'email': 'not-an-email'
    }, follow_redirects=True)

    # Should return 200 and contain the validation messages in HTML
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Full name must be at least 2 characters long.' in body
    assert 'Please enter a valid Philippine phone number' in body
    assert 'Please enter a valid email address.' in body
