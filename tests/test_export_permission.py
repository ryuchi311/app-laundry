import os
import sys
import pytest  # type: ignore

# Make sure project root is on sys.path for test discovery
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User


@pytest.fixture
def app_instance(tmp_path_factory):
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    # Use a temporary sqlite db for testing
    db_fd = tmp_path_factory.mktemp('data') / 'test.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_fd}'
    with app.app_context():
        db.create_all()
        # create a non-admin user
        user = User()
        user.email = 'user@example.com'
        user.password = 'pbkdf2:sha256:150000$test$dummy'  # not used for session-based login
        user.full_name = 'Test User'
        user.role = 'user'
        db.session.add(user)
        db.session.commit()
    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_export_forbidden_for_non_admin(client, app_instance):
    # Log in the created user by writing to the session directly
    app = app_instance
    with app.app_context():
        user = User.query.filter_by(email='user@example.com').first()
    # Set session data to mark user as logged in for the test client
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True

    resp = client.get('/customer/export')
    assert resp.status_code == 403
