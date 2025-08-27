# Minimal Dockerfile for deploying Flask + Flask-SocketIO app to Cloud Run
# Uses official Python slim image

FROM python:3.12-slim

# Install system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev gcc \
    && apt-get install -y --no-install-recommends gettext-base \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Copy only requirements first for Docker layer caching
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Ensure instance folder exists (sqlite db will be created in /home/appuser/app/instance)
RUN mkdir -p instance && chown -R appuser:appuser /home/appuser/app

USER appuser

# Cloud Run listens on PORT env var
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Gunicorn command using eventlet for SocketIO support.
# Use envsubst to expand $PORT into a command template then exec the process (preserves signals).
COPY ./gunicorn_cmd.sh /usr/local/bin/gunicorn_cmd.sh
RUN chmod +x /usr/local/bin/gunicorn_cmd.sh
ENTRYPOINT ["/usr/local/bin/gunicorn_cmd.sh"]
