import os
import time
import urllib.parse
from typing import Optional

import requests  # type: ignore
from flask import current_app

try:
    # Optional: reload env vars when refreshing config
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore


class SMSService:
    """SMS service using Semaphore API"""

    def __init__(self):
        # Initialize with current environment values; will be refreshed per call
        self.api_key = os.environ.get("SEMAPHORE_API_KEY", "")
        self.sender_name = os.environ.get("SEMAPHORE_SENDER_NAME", "ACCIO Laundry")
        self.base_url = "https://semaphore.co/api/v4/messages"
        # Simple in-memory cache for account info to avoid rate limits
        self._account_cache = None  # type: ignore[assignment]
        # Minimum seconds between live account refreshes
        try:
            self.min_refresh_seconds = int(
                os.environ.get("SMS_ACCOUNT_MIN_REFRESH_SECONDS", "60")
            )
        except Exception:
            self.min_refresh_seconds = 60

    def _refresh_config(self) -> None:
        """Refresh API credentials from Flask config or .env at runtime.
        This lets admins update .env without restarting the server.
        """
        # Reload .env into process env if possible
        try:
            if load_dotenv:
                load_dotenv(override=True)  # pick up latest edits
        except Exception:
            pass

        # Prefer Flask app config if available, else fall back to OS env
        api_key = None
        sender = None
        try:
            if current_app:  # type: ignore[truthy-bool]
                api_key = (current_app.config.get("SEMAPHORE_API_KEY") or "").strip()  # type: ignore[attr-defined]
                sender = (current_app.config.get("SEMAPHORE_SENDER_NAME") or "").strip()  # type: ignore[attr-defined]
        except Exception:
            # current_app might not be available outside app context
            pass

        self.api_key = api_key or os.environ.get("SEMAPHORE_API_KEY", "")
        self.sender_name = sender or os.environ.get(
            "SEMAPHORE_SENDER_NAME", "ACCIO Laundry"
        )

    def is_configured(self) -> bool:
        """Check if SMS service is properly configured"""
        self._refresh_config()
        return bool(self.api_key and self.sender_name)

    def format_phone_number(self, phone: Optional[str]) -> Optional[str]:
        """Format phone number for Semaphore API"""
        if not phone:
            return None

        # Remove all non-digits
        phone = "".join(filter(str.isdigit, phone))

        # Handle Philippine phone numbers
        if phone.startswith("63"):
            # Already in international format
            return phone
        elif phone.startswith("0"):
            # Convert 09XXXXXXXXX to 639XXXXXXXXX
            return "63" + phone[1:]
        elif len(phone) == 10 and phone.startswith("9"):
            # Add country code to 9XXXXXXXXX
            return "63" + phone
        else:
            # Return as is if format is unclear
            return phone

    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS using Semaphore API"""
        if not self.is_configured():
            print(
                "SMS service not configured. Please set SEMAPHORE_API_KEY and SEMAPHORE_SENDER_NAME"
            )
            return False

        formatted_phone = self.format_phone_number(phone_number)
        if not formatted_phone:
            print(f"Invalid phone number: {phone_number}")
            return False

        try:
            print(f"Sending SMS to {formatted_phone}...")

            params = {
                "apikey": self.api_key,
                "sendername": self.sender_name,
                "message": message,
                "number": formatted_phone,
            }

            # Build URL with parameters
            url = self.base_url + "?" + urllib.parse.urlencode(params)

            response = requests.post(url, timeout=30)

            if response.status_code == 200:
                print("SMS sent successfully!")
                return True
            else:
                print(f"Failed to send SMS. Status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error sending SMS: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending SMS: {e}")
            return False

    def get_account_status(self) -> dict:
        """Get account status and credit balance from Semaphore API"""
        # Ensure credentials are up to date before checking
        if not self.is_configured():
            return {
                "status": "Not Configured",
                "credit_balance": 0,
                "error": "SMS service not configured",
            }

        # Serve from cache if still fresh
        now = time.time()
        if isinstance(self._account_cache, dict):
            expires_at = self._account_cache.get("expires_at", 0)
            if now < expires_at and self._account_cache.get("data"):
                data = dict(self._account_cache["data"])
                data["cached"] = True
                # seconds remaining until next live refresh attempt
                data["next_refresh_in"] = max(0, int(expires_at - now))
                return data

        try:
            # Semaphore account balance endpoint
            balance_url = "https://semaphore.co/api/v4/account"

            # Try with light backoff to be gentle
            attempts = 0
            last_error = None
            while attempts < 3:
                attempts += 1
                response = requests.get(
                    balance_url, params={"apikey": self.api_key}, timeout=10
                )

                if response.status_code == 200:
                    data = response.json()
                    result = {
                        "status": data.get("account_status", "Active"),
                        "credit_balance": float(data.get("credit_balance", 0)),
                        "account_name": data.get("account_name", self.sender_name),
                        "error": None,
                        "cached": False,
                        "next_refresh_in": max(
                            0, int(max(10, self.min_refresh_seconds))
                        ),
                    }
                    # Cache for a short window to avoid 429s
                    self._account_cache = {
                        "data": result,
                        "expires_at": now + max(10, self.min_refresh_seconds),
                    }
                    return result

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after_header = response.headers.get("Retry-After")
                    try:
                        retry_after = (
                            int(retry_after_header) if retry_after_header else 30
                        )
                    except Exception:
                        retry_after = 30

                    # If we have previous cache, serve it and indicate cooldown
                    if isinstance(
                        self._account_cache, dict
                    ) and self._account_cache.get("data"):
                        cached_data = dict(self._account_cache["data"])
                        cached_data["error"] = (
                            "Rate limited by SMS API; showing last known values."
                        )
                        cached_data["rate_limited_for"] = retry_after
                        cached_data["next_refresh_in"] = retry_after
                        cached_data["cached"] = True
                        # extend cache a bit to avoid hammering
                        self._account_cache["expires_at"] = now + retry_after
                        return cached_data

                    # No cache to fall back to; return a helpful error
                    return {
                        "status": "Error",
                        "credit_balance": 0,
                        "error": f"API Error: 429 - Too Many Attempts. Try again in ~{retry_after}s",
                        "rate_limited_for": retry_after,
                        "next_refresh_in": retry_after,
                        "cached": False,
                    }

                # Non-200 other than 429; collect error and break
                last_error = f"API Error: {response.status_code} - {response.text}"
                break

            # If here, attempts exhausted or non-retryable
            # Return last cache if available; else return error
            if isinstance(self._account_cache, dict) and self._account_cache.get(
                "data"
            ):
                cached_data = dict(self._account_cache["data"])
                cached_data["error"] = last_error or "Unknown API error"
                # keep existing next_refresh_in on cache if present; else compute from expires_at
                if "next_refresh_in" not in cached_data:
                    expires_at = self._account_cache.get("expires_at", now)
                    cached_data["next_refresh_in"] = max(0, int(expires_at - now))
                cached_data["cached"] = True
                return cached_data
            return {
                "status": "Error",
                "credit_balance": 0,
                "error": last_error or "Unknown API error",
                "cached": False,
            }

        except requests.exceptions.RequestException as e:
            return {
                "status": "Connection Error",
                "credit_balance": 0,
                "error": f"Failed to connect to SMS service: {str(e)}",
            }
        except Exception as e:
            return {
                "status": "Error",
                "credit_balance": 0,
                "error": f"Unexpected error: {str(e)}",
            }


# Global SMS service instance
sms_service = SMSService()


def send_sms_notification(phone_number: str, message: str) -> bool:
    """Convenience function to send SMS notification"""
    return sms_service.send_sms(phone_number, message)


def send_laundry_status_sms(customer, laundry, status: str) -> bool:
    """Send laundry status update via SMS"""
    # Refresh configuration to pick up any runtime changes
    try:
        sms_service._refresh_config()
    except Exception:
        pass
    if not customer.phone:
        print(f"No phone number for customer {customer.full_name}")
        return False

    # Import here to avoid circular imports
    from .models import SMSSettings

    # Get SMS settings
    settings = SMSSettings.get_settings()

    # Check if SMS is enabled for this status
    status_enabled_map = {
        "Received": settings.received_enabled,
        "Ready for Pickup": settings.ready_pickup_enabled,
        "Completed": settings.completed_enabled,
    }

    # Be conservative: unknown statuses should not send SMS by default
    if not status_enabled_map.get(status, False):
        print(f"SMS notifications disabled for status: {status}")
        return False

    # Get custom message template
    message_template_map = {
        "Received": settings.received_message,
        "Ready for Pickup": settings.ready_pickup_message,
        "Completed": settings.completed_message,
    }

    template = message_template_map.get(status)
    if template:
        try:
            message = settings.format_message(
                template,
                customer.full_name,
                str(laundry.laundry_id),
                sms_service.sender_name,
                number_of_items=getattr(laundry, "item_count", None),
            )
        except Exception as e:
            print(f"Error formatting SMS template for status {status}: {e}")
            message = f"Hi {customer.full_name}! Your laundry (#{laundry.laundry_id}) status: {status}. - {sms_service.sender_name}"
    else:
        # Fallback message if no template found
        message = f"Hi {customer.full_name}! Your laundry (#{laundry.laundry_id}) status has been updated to: {status}. - {sms_service.sender_name}"

    return send_sms_notification(customer.phone, message)


def send_welcome_sms(customer) -> bool:
    """Send welcome SMS to new customer"""
    if not customer.phone:
        return False

    # Import here to avoid circular imports
    from .models import SMSSettings

    # Get SMS settings
    settings = SMSSettings.get_settings()

    # Check if welcome SMS is enabled
    if not settings.welcome_enabled:
        print("Welcome SMS notifications are disabled")
        return False

    # Format welcome message
    message = settings.format_message(
        settings.welcome_message,
        customer.full_name,
        "",  # No laundry ID for welcome message
        sms_service.sender_name,
    )

    return send_sms_notification(customer.phone, message)
