Cloud Run deployment notes
==========================

This document describes environment variables and a simple Cloud Build pipeline to build and deploy the app to Cloud Run.

Required environment variables (set in Cloud Run service settings or via Cloud Build substitutions):

- SECRET_KEY: A secure random string for Flask.
- DATABASE_URL: SQLAlchemy-compatible database URL (e.g., Cloud SQL connection string or managed Postgres URL). Do not use the default SQLite in multi-instance setups.
- MAIL_USERNAME and MAIL_PASSWORD: For sending emails (optional).
- SEMAPHORE_API_KEY and SEMAPHORE_SENDER_NAME: For SMS sending (optional).

Recommended Cloud Run settings:
- Set concurrency to 80 (default) or lower if you expect heavy CPU usage per request.
- Use at least 512Mi memory for eventlet/Gunicorn workloads; increase if needed.
- Configure a health check that calls /healthz (responds 200 when DB reachable).

Deploy using Cloud Build (example):

1. Submit a build manually:

   gcloud builds submit --config cloudbuild.yaml --substitutions=_SECRET_KEY="<secret>",_DATABASE_URL="<db_url>"

2. Or set up a Cloud Build trigger on your repo to automatically build on push.

Notes:
- The container entrypoint uses gunicorn with the eventlet worker to support Socket.IO.
- Ensure you provide a production-ready database via DATABASE_URL for multi-instance deployments.
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
