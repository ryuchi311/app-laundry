"""Headless tests for SMS settings endpoints using Flask test client.

This script starts the Flask app context and performs a few requests to
exercise the sms-settings blueprint without starting the server.
"""

from app import create_app, db
from app.models import SMSSettings, SMSSettingsProfile
import json

app = create_app()

with app.app_context():
    client = app.test_client()
    # Create test user via signup (first user will be super_admin if none exists)
    print("POST /auth/signup to create test user")
    resp = client.post(
        "/auth/signup",
        data={
            "email": "test@example.com",
            "fullName": "Test User",
            "phone": "+639171234567",
            "password1": "password123",
            "password2": "password123",
        },
        follow_redirects=True,
    )
    print("signup status:", resp.status_code)

    # Login the test user
    print("POST /auth/login to authenticate test user")
    resp = client.post(
        "/auth/login",
        data={"email": "test@example.com", "password": "password123"},
        follow_redirects=True,
    )
    print("login status:", resp.status_code)

    # Now call SMS endpoints while authenticated
    print("GET /sms-settings/sms-settings (render template)")
    resp = client.get("/sms-settings/sms-settings")
    print("status_code:", resp.status_code)

    print("GET /sms-settings/sms-settings/profiles")
    resp = client.get("/sms-settings/sms-settings/profiles")
    print("status_code:", resp.status_code, "data:", resp.get_json())

    # Get active profile id (if any)
    profiles = resp.get_json() or {}
    profs = profiles.get("profiles", [])
    if profs:
        pid = profs[0]["id"]
        print(f"GET /sms-settings/sms-settings/profiles/{pid}")
        resp = client.get(f"/sms-settings/sms-settings/profiles/{pid}", follow_redirects=True)
        print("status_code:", resp.status_code, "data keys:", list((resp.get_json() or {}).keys()))

    print("POST /sms-settings/sms-settings/preview")
    resp = client.post("/sms-settings/sms-settings/preview", data={"message": "Hi {customer_name}, test",}, follow_redirects=True)
    print("status_code:", resp.status_code, "json:", resp.get_json())

    print("POST /sms-settings/sms-settings/test (custom) - missing phone")
    resp = client.post("/sms-settings/sms-settings/test", data={"message_type": "custom", "custom_message": "Hello"}, follow_redirects=True)
    print("status_code:", resp.status_code, "json:", resp.get_json())

    print("POST /sms-settings/sms-settings/reset")
    resp = client.post("/sms-settings/sms-settings/reset", follow_redirects=True)
    print("status_code:", resp.status_code)

    print("Done")
