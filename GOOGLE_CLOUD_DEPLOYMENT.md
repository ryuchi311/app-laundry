# 🚀 Google Cloud Deployment Guide
## Laundry Management System

Your project is now ready for Google Cloud deployment! Follow these steps to deploy your application.

## 📋 Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed
3. **Your project files** ready (already prepared)

## 🛠️ Step 1: Install Google Cloud SDK

### Windows:
1. Download from [cloud.google.com/sdk](https://cloud.google.com/sdk)
2. Run the installer
3. Restart command prompt

### Mac/Linux:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### Verify Installation:
```bash
gcloud version
```

## 🔐 Step 2: Setup Google Cloud Project

Open terminal in your project directory (`d:\app-laundry`) and run:

```bash
# 1. Login to Google Cloud
gcloud auth login

# 2. Create a new project (replace 'laundry-app-2025' with your preferred name)
gcloud projects create laundry-app-2025 --name="Laundry Management System"

# 3. Set the project as default
gcloud config set project laundry-app-2025

# 4. Enable required APIs
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 5. Initialize App Engine (choose region close to your location)
gcloud app create --region=us-central1
```

## 📝 Step 3: Configure Environment Variables

Before deploying, update the `app.yaml` file with your secure secret key:

1. Open `app.yaml`
2. Replace `"your-super-secure-secret-key-change-this-in-production"` with a secure random string
3. Add any other environment variables you need:

```yaml
env_variables:
  FLASK_ENV: production
  SECRET_KEY: "your-actual-secure-secret-key-here"
  SEMAPHORE_API_KEY: "your-sms-api-key"
  SEMAPHORE_SENDER_NAME: "YourBusiness"
```

## 🚀 Step 4: Deploy to Google Cloud

```bash
# Deploy your application
gcloud app deploy app.yaml --version=v1

# View your deployed app
gcloud app browse
```

## 🗄️ Step 5: Initialize Production Database

After successful deployment, initialize your database:

```bash
# Run the production database setup
python setup_production_db.py
```

This will create:
- ✅ Admin user (admin@laundry.com / admin123)
- ✅ Manager user (manager@laundry.com / manager123)  
- ✅ Business settings
- ✅ SMS settings
- ✅ Sample customers and services

## 🔒 Step 6: Secure Your Application

1. **Change Default Passwords**:
   - Login to your deployed app
   - Go to User Management
   - Change admin and manager passwords

2. **Configure SMS Service**:
   - Go to SMS Settings
   - Add your Semaphore API credentials
   - Test SMS functionality

3. **Update Business Information**:
   - Go to Business Settings
   - Update with your actual business details

## 🌐 Step 7: Custom Domain (Optional)

```bash
# Add custom domain
gcloud app domain-mappings create yourdomain.com

# Update your domain's DNS settings:
# A record: @ -> ghs.googlehosted.com
# CNAME record: www -> ghs.googlehosted.com
```

## 📊 Step 8: Monitor Your Application

```bash
# View logs
gcloud app logs tail -s default

# Check app versions
gcloud app versions list

# View metrics
gcloud app open-console
```

## 🔄 Step 9: Update Your Application

When you make changes:

```bash
# Deploy new version
gcloud app deploy --version=v2

# Migrate traffic to new version
gcloud app services set-traffic default --splits v2=1
```

## 📱 Your Live Application

After deployment:
- **URL**: `https://laundry-app-2025.appspot.com`
- **Custom Domain**: `https://yourdomain.com` (if configured)

## 💰 Cost Estimation

Typical monthly costs:
- **Small business** (< 100 customers): $10-25
- **Medium business** (100-500 customers): $25-75  
- **Large business** (500+ customers): $75-200

## 🆘 Troubleshooting

### Common Issues:

**1. Deployment Fails:**
```bash
# Check logs
gcloud app logs tail -s default --level=debug

# Verify project settings
gcloud config list
```

**2. Database Issues:**
```bash
# Run database setup again
python setup_production_db.py

# Check app logs
gcloud app logs tail -s default
```

**3. Static Files Not Loading:**
- Verify `static/` folder exists
- Check `app.yaml` static handlers

### Get Help:
- [Google Cloud Support](https://cloud.google.com/support)
- [App Engine Documentation](https://cloud.google.com/appengine/docs)

## ✅ Deployment Checklist

Before going live:

- [ ] Google Cloud project created
- [ ] App deployed successfully  
- [ ] Database initialized
- [ ] Admin password changed
- [ ] SMS service configured
- [ ] Business settings updated
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Monitoring set up
- [ ] Backup strategy planned

## 🎉 Success!

Your Laundry Management System is now running on Google Cloud with:
- ✅ Automatic scaling
- ✅ High availability  
- ✅ Global CDN
- ✅ Secure HTTPS
- ✅ Professional reliability

**Next Steps:**
1. Login and change default passwords
2. Configure your SMS service
3. Add your real customers and services
4. Customize business settings
5. Start managing your laundry business!

---

*Your application is now live and ready for production use! 🚀*
