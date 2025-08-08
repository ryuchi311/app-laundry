from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import SMSSettings
from . import db
from .sms_service import sms_service, send_sms_notification

sms_settings_bp = Blueprint('sms_settings', __name__)

@sms_settings_bp.route('/sms-settings', methods=['GET', 'POST'])
@login_required
def sms_settings():
    """SMS Settings Configuration Page"""
    settings = SMSSettings.get_settings()
    
    if request.method == 'POST':
        try:
            # Update enable/disable settings
            settings.received_enabled = 'received_enabled' in request.form
            settings.in_process_enabled = 'in_process_enabled' in request.form
            settings.ready_pickup_enabled = 'ready_pickup_enabled' in request.form
            settings.completed_enabled = 'completed_enabled' in request.form
            settings.welcome_enabled = 'welcome_enabled' in request.form
            
            # Update message templates
            settings.received_message = request.form.get('received_message', '').strip()
            settings.in_process_message = request.form.get('in_process_message', '').strip()
            settings.ready_pickup_message = request.form.get('ready_pickup_message', '').strip()
            settings.completed_message = request.form.get('completed_message', '').strip()
            settings.welcome_message = request.form.get('welcome_message', '').strip()
            
            # Update metadata
            settings.updated_by = current_user.id
            
            db.session.commit()
            flash('SMS settings updated successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating SMS settings: {str(e)}', 'error')
    
    # Get SMS service configuration status
    sms_configured = sms_service.is_configured()
    
    return render_template('sms_settings.html', 
                         settings=settings, 
                         sms_configured=sms_configured,
                         sender_name=sms_service.sender_name)

@sms_settings_bp.route('/sms-settings/test', methods=['POST'])
@login_required
def test_sms():
    """Test SMS functionality"""
    phone = request.form.get('test_phone', '').strip()
    message_type = request.form.get('message_type', 'custom')
    custom_message = request.form.get('custom_message', '').strip()
    
    if not phone:
        return jsonify({'success': False, 'message': 'Phone number is required'})
    
    if not sms_service.is_configured():
        return jsonify({'success': False, 'message': 'SMS service is not configured'})
    
    try:
        settings = SMSSettings.get_settings()
        
        # Generate test message based on type
        if message_type == 'received':
            if not settings.received_enabled:
                return jsonify({'success': False, 'message': 'Received notifications are disabled'})
            message = settings.format_message(settings.received_message, 'John Doe', 'TEST001', sms_service.sender_name)
        elif message_type == 'in_process':
            if not settings.in_process_enabled:
                return jsonify({'success': False, 'message': 'In Process notifications are disabled'})
            message = settings.format_message(settings.in_process_message, 'John Doe', 'TEST001', sms_service.sender_name)
        elif message_type == 'ready_pickup':
            if not settings.ready_pickup_enabled:
                return jsonify({'success': False, 'message': 'Ready for Pickup notifications are disabled'})
            message = settings.format_message(settings.ready_pickup_message, 'John Doe', 'TEST001', sms_service.sender_name)
        elif message_type == 'completed':
            if not settings.completed_enabled:
                return jsonify({'success': False, 'message': 'Completed notifications are disabled'})
            message = settings.format_message(settings.completed_message, 'John Doe', 'TEST001', sms_service.sender_name)
        elif message_type == 'welcome':
            if not settings.welcome_enabled:
                return jsonify({'success': False, 'message': 'Welcome notifications are disabled'})
            message = settings.format_message(settings.welcome_message, 'John Doe', '', sms_service.sender_name)
        elif message_type == 'custom':
            if not custom_message:
                return jsonify({'success': False, 'message': 'Custom message is required'})
            message = custom_message
        else:
            return jsonify({'success': False, 'message': 'Invalid message type'})
        
        # Send test SMS
        success = send_sms_notification(phone, message)
        
        if success:
            return jsonify({'success': True, 'message': 'Test SMS sent successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send test SMS'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error sending test SMS: {str(e)}'})

@sms_settings_bp.route('/sms-settings/reset', methods=['POST'])
@login_required
def reset_messages():
    """Reset SMS messages to default"""
    try:
        settings = SMSSettings.get_settings()
        
        # Reset to default messages
        settings.received_message = "Hi {customer_name}! Your laundry (#{laundry_id}) has been received and is being processed. - {sender_name}"
        settings.in_process_message = "Hi {customer_name}! Your laundry (#{laundry_id}) is now being processed. We'll notify you when it's ready! - {sender_name}"
        settings.ready_pickup_message = "Hi {customer_name}! Great news! Your laundry (#{laundry_id}) is ready for pickup. Please visit us during business hours. - {sender_name}"
        settings.completed_message = "Hi {customer_name}! Your laundry (#{laundry_id}) has been completed. Thank you for choosing {sender_name}!"
        settings.welcome_message = "Welcome to {sender_name}, {customer_name}! We're excited to serve you. For inquiries, contact us at +639761111464."
        
        # Update metadata
        settings.updated_by = current_user.id
        
        db.session.commit()
        flash('SMS messages reset to default successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting SMS messages: {str(e)}', 'error')
    
    return redirect(url_for('sms_settings.sms_settings'))

@sms_settings_bp.route('/sms-settings/preview', methods=['POST'])
@login_required
def preview_message():
    """Preview formatted message"""
    try:
        message_template = request.form.get('message', '')
        settings = SMSSettings.get_settings()
        
        # Preview with sample data
        formatted_message = settings.format_message(
            message_template,
            'John Doe',
            'L001234',
            sms_service.sender_name
        )
        
        return jsonify({'success': True, 'preview': formatted_message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error previewing message: {str(e)}'})

@sms_settings_bp.route('/sms-settings/bulk-message', methods=['GET', 'POST'])
@login_required
def bulk_message():
    """Send bulk promotional/event messages to all customers"""
    from .models import Customer, BulkMessageHistory
    
    if request.method == 'POST':
        message_text = request.form.get('message_text', '').strip()
        message_type = request.form.get('message_type', 'promo')
        send_to_all = request.form.get('send_to_all') == 'on'
        
        if not message_text:
            flash('Message text is required', 'error')
            return redirect(url_for('sms_settings.bulk_message'))
            
        if not sms_service.is_configured():
            flash('SMS service is not configured. Please set up your API credentials first.', 'error')
            return redirect(url_for('sms_settings.bulk_message'))
        
        # Get all customers with phone numbers
        customers = Customer.query.filter(Customer.phone.isnot(None)).all()
        customers_with_phones = [c for c in customers if c.phone and c.phone.strip()]
        
        if not customers_with_phones:
            flash('No customers found with phone numbers', 'warning')
            return redirect(url_for('sms_settings.bulk_message'))
        
        # Create bulk message history record
        bulk_history = BulkMessageHistory()
        bulk_history.message_text = message_text
        bulk_history.message_type = message_type
        bulk_history.sent_by_user_id = current_user.id
        bulk_history.total_recipients = len(customers_with_phones)
        db.session.add(bulk_history)
        
        success_count = 0
        failed_count = 0
        
        for customer in customers_with_phones:
            try:
                # Format message with customer name and sender name
                formatted_message = message_text.replace('{customer_name}', customer.full_name)
                formatted_message = formatted_message.replace('{sender_name}', sms_service.sender_name)
                
                if sms_service.send_sms(customer.phone, formatted_message):
                    success_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                print(f"Error sending SMS to {customer.full_name}: {str(e)}")
        
        # Update bulk message history with results
        bulk_history.successful_sends = success_count
        bulk_history.failed_sends = failed_count
        db.session.commit()
        
        if success_count > 0:
            flash(f'Bulk message sent successfully to {success_count} customers!', 'success')
        if failed_count > 0:
            flash(f'Failed to send message to {failed_count} customers', 'warning')
            
        return redirect(url_for('sms_settings.bulk_message'))
    
    # GET request - show the form
    from .models import Customer, BulkMessageHistory
    total_customers = Customer.query.count()
    customers_with_phones = Customer.query.filter(Customer.phone.isnot(None)).count()
    
    # Get recent bulk message history
    recent_campaigns = BulkMessageHistory.query.order_by(BulkMessageHistory.sent_at.desc()).limit(5).all()
    
    return render_template('bulk_message.html',
                         total_customers=total_customers,
                         customers_with_phones=customers_with_phones,
                         recent_campaigns=recent_campaigns,
                         sms_configured=sms_service.is_configured())

@sms_settings_bp.route('/sms-settings/customer-list')
@login_required
def customer_list():
    """Get list of customers for bulk messaging preview"""
    from .models import Customer
    
    customers = Customer.query.filter(Customer.phone.isnot(None)).all()
    customer_data = []
    
    for customer in customers:
        if customer.phone and customer.phone.strip():
            customer_data.append({
                'id': customer.id,
                'name': customer.full_name,
                'phone': customer.phone,
                'email': customer.email or 'N/A'
            })
    
    return jsonify({'customers': customer_data})

@sms_settings_bp.route('/sms-settings/preview-bulk', methods=['POST'])
@login_required
def preview_bulk_message():
    """Preview how bulk message will look"""
    message_text = request.form.get('message_text', '')
    customer_name = request.form.get('sample_customer_name', 'John Doe')
    
    if not message_text:
        return jsonify({'success': False, 'message': 'Message text is required'})
    
    try:
        # Format message with sample data
        formatted_message = message_text.replace('{customer_name}', customer_name)
        formatted_message = formatted_message.replace('{sender_name}', sms_service.sender_name)
        
        return jsonify({
            'success': True, 
            'preview': formatted_message,
            'length': len(formatted_message)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error previewing message: {str(e)}'})
