from app import create_app
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

TEST_EMAIL = "test+qr@example.com"
TEST_PASS = "testpass"
LAUNDRY_ID = "1665612416"

app = create_app()

with app.app_context():
    # Ensure test user exists
    user = User.query.filter_by(email=TEST_EMAIL).first()
    if not user:
        user = User()
        user.email = TEST_EMAIL
        user.full_name = "QR Test User"
        user.password = generate_password_hash(TEST_PASS)
        user.role = "admin"
        user.is_active = True
        db.session.add(user)
        db.session.commit()

with app.test_client() as c:
    # Login
    rv = c.post("/auth/login", data={"email": TEST_EMAIL, "password": TEST_PASS}, follow_redirects=True)
    print("Login status:", rv.status_code)

    # Request receipt
    rv = c.get(f"/laundry/receipt/{LAUNDRY_ID}")
    print("Receipt GET status:", rv.status_code)
    body = rv.get_data(as_text=True)
    has_qr = "data:image/png;base64," in body
    print("Has QR:", has_qr)
    if has_qr:
        start = body.find('data:image/png;base64,')
        print(body[start:start+200])
