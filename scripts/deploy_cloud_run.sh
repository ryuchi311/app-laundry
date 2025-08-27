#!/usr/bin/env bash
set -euo pipefail

# Deploy the app to Cloud Run and wire Cloud SQL (unix-socket) access.
# Usage:
#   ./scripts/deploy_cloud_run.sh \
#     <PROJECT_ID> <REGION> <SERVICE_NAME> <IMAGE_TAG> <INSTANCE_CONNECTION_NAME> <DATABASE_URL> <SECRET_KEY>
#
# Example DATABASE_URL for Postgres using pg8000 + Cloud SQL unix socket:
#   postgresql+pg8000://dbuser:dbpass@/dbname?unix_sock=/cloudsql/PROJECT:REGION:INSTANCE/.s.PGSQL.5432
#
# Notes:
# - This script uses Cloud Build to build and push the image to Container Registry (gcr.io).
# - It then deploys to Cloud Run and attaches the specified Cloud SQL instance.
# - You can instead provide a DATABASE_URL that references a managed DB service.

if [ "$#" -lt 7 ]; then
  echo "Usage: $0 PROJECT_ID REGION SERVICE_NAME IMAGE_TAG INSTANCE_CONNECTION_NAME DATABASE_URL SECRET_KEY"
  exit 2
fi

PROJECT_ID="$1"
REGION="$2"
SERVICE_NAME="$3"
IMAGE_TAG="$4"
INSTANCE_CONNECTION_NAME="$5"
DATABASE_URL="$6"
SECRET_KEY="$7"

IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:${IMAGE_TAG}"

echo "Building image ${IMAGE} with Cloud Build..."
gcloud builds submit --tag "${IMAGE}"

echo "Deploying to Cloud Run service ${SERVICE_NAME} in ${REGION}..."
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --set-env-vars "DATABASE_URL=${DATABASE_URL},SECRET_KEY=${SECRET_KEY}" \
  --memory 512Mi \
  --concurrency 80

echo "Deployment complete. To view the service URL run:"
echo "  gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)'"
