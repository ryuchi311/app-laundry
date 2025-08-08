import requests  # type: ignore
import urllib.parse
import os
from typing import Optional
from flask import current_app

class SMSService:
    """SMS service using Semaphore API"""
    
    def __init__(self):
        self.api_key = os.environ.get('SEMAPHORE_API_KEY', '')
        self.sender_name = os.environ.get('SEMAPHORE_SENDER_NAME', 'ACCIO Laundry')
        self.base_url = 'https://semaphore.co/api/v4/messages'
    
    def is_configured(self) -> bool:
        """Check if SMS service is properly configured"""
        return bool(self.api_key and self.sender_name)
    
    def format_phone_number(self, phone: Optional[str]) -> Optional[str]:
        """Format phone number for Semaphore API"""
        if not phone:
            return None
            
        # Remove all non-digits
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle Philippine phone numbers
        if phone.startswith('63'):
            # Already in international format
            return phone
        elif phone.startswith('0'):
            # Convert 09XXXXXXXXX to 639XXXXXXXXX
            return '63' + phone[1:]
        elif len(phone) == 10 and phone.startswith('9'):
            # Add country code to 9XXXXXXXXX
            return '63' + phone
        else:
            # Return as is if format is unclear
            return phone
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS using Semaphore API"""
        if not self.is_configured():
            print("SMS service not configured. Please set SEMAPHORE_API_KEY and SEMAPHORE_SENDER_NAME")
            return False
        
        formatted_phone = self.format_phone_number(phone_number)
        if not formatted_phone:
            print(f"Invalid phone number: {phone_number}")
            return False
        
        try:
            print(f"Sending SMS to {formatted_phone}...")
            
            params = {
                'apikey': self.api_key,
                'sendername': self.sender_name,
                'message': message,
                'number': formatted_phone
            }
            
            # Build URL with parameters
            url = self.base_url + '?' + urllib.parse.urlencode(params)
            
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

# Global SMS service instance
sms_service = SMSService()

def send_sms_notification(phone_number: str, message: str) -> bool:
    """Convenience function to send SMS notification"""
    return sms_service.send_sms(phone_number, message)

def send_laundry_status_sms(customer, laundry, status: str) -> bool:
    """Send laundry status update via SMS"""
    if not customer.phone:
        print(f"No phone number for customer {customer.full_name}")
        return False
    
    # Import here to avoid circular imports
    from .models import SMSSettings
    
    # Get SMS settings
    settings = SMSSettings.get_settings()
    
    # Check if SMS is enabled for this status
    status_enabled_map = {
        'Received': settings.received_enabled,
        'In Process': settings.in_process_enabled,
        'Ready for Pickup': settings.ready_pickup_enabled,
        'Completed': settings.completed_enabled
    }
    
    if not status_enabled_map.get(status, True):
        print(f"SMS notifications disabled for status: {status}")
        return False
    
    # Get custom message template
    message_template_map = {
        'Received': settings.received_message,
        'In Process': settings.in_process_message,
        'Ready for Pickup': settings.ready_pickup_message,
        'Completed': settings.completed_message
    }
    
    template = message_template_map.get(status)
    if template:
        message = settings.format_message(
            template, 
            customer.full_name, 
            str(laundry.laundry_id), 
            sms_service.sender_name
        )
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
        sms_service.sender_name
    )
    
    return send_sms_notification(customer.phone, message)
