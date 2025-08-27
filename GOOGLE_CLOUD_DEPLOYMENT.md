# Google Cloud Deployment Guide

This project is ready for deployment to Google Cloud Run.

## Prerequisites
- Google Cloud project with billing enabled
- Cloud Run and Cloud Build APIs enabled
- gcloud CLI installed and authenticated

## Build and Deploy

1. **Build and push container image:**

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/app-laundry
```

2. **Deploy to Cloud Run:**

```bash
gcloud run deploy app-laundry \
  --image gcr.io/PROJECT_ID/app-laundry \
  --platform managed \
  --region REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --port 8080
```

## Environment Variables
Set these in Cloud Run:
- `SECRET_KEY`
- `MAIL_USERNAME`, `MAIL_PASSWORD`
- `SEMAPHORE_API_KEY`, `SEMAPHORE_SENDER_NAME`
- For production, update `SQLALCHEMY_DATABASE_URI` to use Cloud SQL (Postgres/MySQL)

## Dockerfile Lint (CI)
A GitHub Actions workflow is included to lint your Dockerfile on every push/PR:
- `.github/workflows/docker-lint.yml` uses `hadolint` to check for best practices.

## Notes
- Default DB is SQLite (not recommended for production). Use Cloud SQL and update config in `app/__init__.py`.
- Flask-SocketIO uses eventlet; Gunicorn runs with eventlet worker for compatibility.
- For background tasks, consider Cloud Tasks or Pub/Sub + Cloud Run.

## References
- [Cloud Run Quickstart](https://cloud.google.com/run/docs/quickstarts/build-and-deploy)
- [Cloud SQL for Flask](https://cloud.google.com/sql/docs/mysql/connect-run)
- [Hadolint Dockerfile Linter](https://github.com/hadolint/hadolint)
