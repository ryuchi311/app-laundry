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

Cloud SQL (recommended for multi-instance deployments)

If you deploy multiple Cloud Run instances you must not use SQLite. Use Cloud SQL (Postgres or MySQL) and set
`DATABASE_URL` to a SQLAlchemy-compatible URL. For Cloud SQL we recommend using the unix socket path exposed
to the container by the Cloud Run Cloud SQL connector. Examples:

- Postgres (pg8000 driver) via unix socket:

   postgresql+pg8000://DB_USER:DB_PASS@/DB_NAME?unix_sock=/cloudsql/PROJECT:REGION:INSTANCE/.s.PGSQL.5432

- MySQL (pymysql driver) via unix socket:

   mysql+pymysql://DB_USER:DB_PASS@/DB_NAME?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE

When deploying with the Cloud Run console or `gcloud run deploy`, add the `--add-cloudsql-instances` flag with your
instance connection name (PROJECT:REGION:INSTANCE). The `deploy_cloud_run.sh` script included in `scripts/` automates
these steps.

Secrets and best practices
- Store `SECRET_KEY`, DB credentials, and other secrets in Secret Manager and mount them as environment variables in
   Cloud Run. Avoid checking secrets into repository or passing them on the command line in CI logs.

Deploy script
----------------
Use the provided script to build and deploy (wires Cloud SQL):

```bash
./scripts/deploy_cloud_run.sh PROJECT_ID REGION SERVICE_NAME IMAGE_TAG INSTANCE_CONNECTION_NAME DATABASE_URL SECRET_KEY
```

Replace placeholders accordingly. The script will run `gcloud builds submit` and then `gcloud run deploy` with the
`--add-cloudsql-instances` option.

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
