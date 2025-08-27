FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable stdout/stderr flushing
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# Install build deps required for some packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install as root (so non-root user can run packages)
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

# Copy application code
COPY . /app

# Ensure entrypoint is executable (do this as root to avoid permission issues)
COPY gunicorn_cmd.sh /usr/local/bin/gunicorn_cmd.sh
RUN chmod +x /usr/local/bin/gunicorn_cmd.sh

# Create a non-root user and take ownership of the app directory
RUN useradd --create-home appuser && chown -R appuser:appuser /app

USER appuser
WORKDIR /app

# Expose the default port (Cloud Run provides $PORT at runtime)
EXPOSE 8080

ENV PORT=8080

ENTRYPOINT ["/usr/local/bin/gunicorn_cmd.sh"]
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

# Copy entrypoint script to a system path and make it executable (run as root)
COPY ./gunicorn_cmd.sh /usr/local/bin/gunicorn_cmd.sh
RUN chmod +x /usr/local/bin/gunicorn_cmd.sh && chown root:root /usr/local/bin/gunicorn_cmd.sh

USER appuser

# Cloud Run listens on PORT env var
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Gunicorn command using eventlet for SocketIO support.
# The entrypoint script will exec gunicorn and preserve signals.
ENTRYPOINT ["/usr/local/bin/gunicorn_cmd.sh"]
