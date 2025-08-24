This project includes configuration to deploy the Flask app to Google Cloud Run.

Quick deploy (gcloud):

1. Build and push image:

   gcloud builds submit --tag gcr.io/PROJECT_ID/app-laundry

2. Deploy to Cloud Run:

   gcloud run deploy app-laundry \
     --image gcr.io/PROJECT_ID/app-laundry \
     --platform managed \
     --region REGION \
     --allow-unauthenticated \
     --memory 512Mi \
     --port 8080

Notes:
- The app uses SQLite by default (instance/laundry.db). For production use, switch to a managed DB (Cloud SQL) and update `app/__init__.py` SQLALCHEMY_DATABASE_URI accordingly.
- Environment variables to set in Cloud Run: SECRET_KEY, MAIL_USERNAME, MAIL_PASSWORD, SEMAPHORE_API_KEY, SEMAPHORE_SENDER_NAME.
- Flask-SocketIO uses eventlet for async support; the Dockerfile installs `eventlet` and runs Gunicorn with the `eventlet` worker.
- To use Cloud SQL, set up a Cloud SQL instance and provide the connection via the Cloud SQL Proxy or the Cloud Run Cloud SQL connector.
