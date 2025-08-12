# SMS Notifications Setup Guide

## Overview
The ACCIO Laundry Management System now supports SMS notifications using the Semaphore API service. Customers will automatically receive SMS updates about their laundry status, and new customers will receive welcome messages.

## Features
- ✅ **Welcome SMS** - Sent to new customers when they're added to the system
- ✅ **Status Updates** - Automatic SMS when laundry status changes
- ✅ **Ready for Pickup** - Notification when laundry is ready
- ✅ **Completion Alerts** - Confirmation when laundry is completed
- ✅ **Philippine Mobile Support** - Supports both 09XXXXXXXXX and +639XXXXXXXXX formats

## Setup Instructions

### 1. Get Semaphore API Credentials
1. Visit [https://semaphore.co](https://semaphore.co)
2. Create an account or log in
3. Navigate to your dashboard
4. Copy your **API Key**
5. Register or choose your **Sender Name** (max 11 characters)

### 2. Configure in the Application
1. Open your laundry management system
2. Click the menu dropdown (top right)
3. Select **"SMS Notifications"**
4. Enter your Semaphore API Key
5. Enter your Sender Name
6. Optionally add a test phone number
7. Click **"Save SMS Settings"**

### 3. Test the Configuration
- If you provided a test number, you should receive a test SMS
- Add a new customer with a phone number to test welcome SMS
- Update a laundry status to test status notifications

## Automatic Notifications

### When New Customer is Added
```
Welcome to ACCIO Laundry, [Customer Name]! We're excited to serve you. 
For inquiries, contact us at +639761111464. - ACCIO Laundry
```

### When Laundry Status Changes

**Received:**
```
Hi [Customer Name]! Your laundry (#[ID]) has been received and is being processed. - ACCIO Laundry
```

**In Process:**
```
Hi [Customer Name]! Your laundry (#[ID]) is now being processed. We'll notify you when it's ready! - ACCIO Laundry
```

**Ready for Pickup:**
```
Hi [Customer Name]! Great news! Your laundry (#[ID]) is ready for pickup. 
Please visit us during business hours. - ACCIO Laundry
```

**Completed:**
```
Hi [Customer Name]! Your laundry (#[ID]) has been completed. Thank you for choosing ACCIO Laundry!
```

## Phone Number Format Support
The system automatically handles various Philippine phone number formats:
- `09123456789` → Converted to `639123456789`
- `+639123456789` → Used as is
- `9123456789` → Converted to `639123456789`
- `639123456789` → Used as is

## Troubleshooting

### SMS Not Being Sent
1. **Check API Key**: Ensure your Semaphore API key is correct
2. **Check Credits**: Verify you have SMS credits in your Semaphore account
3. **Check Sender Name**: Ensure sender name is registered and approved
4. **Check Phone Format**: Verify phone numbers are in valid format
5. **Check Logs**: Look at the Flask console for error messages

### Common Issues
- **"SMS service not configured"**: API key or sender name is missing
- **"Invalid phone number"**: Phone number format is incorrect
- **HTTP errors**: Network issues or invalid API credentials
- **No response**: Semaphore service might be down

## Environment Variables (Optional)
For production deployment, you can set environment variables:
```bash
export SEMAPHORE_API_KEY="your_api_key_here"
export SEMAPHORE_SENDER_NAME="ACCIO Laundry"
```

Or create a `.env` file (copy from `.env.example`):
```
SEMAPHORE_API_KEY=your_api_key_here
SEMAPHORE_SENDER_NAME=ACCIO Laundry
```

## Cost Considerations
- Each SMS sent through Semaphore has a cost
- Check Semaphore pricing at [https://semaphore.co/pricing](https://semaphore.co/pricing)
- Monitor your usage through the Semaphore dashboard
- Consider setting up low credit alerts in your Semaphore account

## API Documentation
For advanced configuration, refer to:
- [Semaphore API Documentation](https://semaphore.co/docs)
- [SMS API Reference](https://semaphore.co/docs#send-sms)

## Support
If you encounter issues:
1. Check this documentation first
2. Review the Semaphore documentation
3. Check your Semaphore account dashboard
4. Verify your network connection
5. Contact Semaphore support for API-related issues

## Security Notes
- Never commit your `.env` file or API keys to version control
- Keep your API key secure and don't share it
- Regularly monitor your Semaphore account for unusual activity
- Use environment variables for production deployments
