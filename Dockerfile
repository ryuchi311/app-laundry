
FROM python:3.12-slim

# Install system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser/app

# Copy only requirements first for Docker layer caching
# Copy and install only requirements first for better layer caching
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code (including templates/)
# Copy app source
COPY . .

# Ensure instance folder exists (sqlite db will be created in /home/appuser/app/instance)
RUN mkdir -p instance && chown -R appuser:appuser /home/appuser/app

# Copy entrypoint script to a system path, make it executable and owned by root
COPY ./gunicorn_cmd.sh /usr/local/bin/gunicorn_cmd.sh
RUN chmod +x /usr/local/bin/gunicorn_cmd.sh && chown root:root /usr/local/bin/gunicorn_cmd.sh

# Run as non-root user
USER appuser

# Cloud Run listens on PORT env var
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the default Cloud Run port
EXPOSE 8080

# Use the entrypoint script which exec's gunicorn so signals flow correctly
ENTRYPOINT ["/usr/local/bin/gunicorn_cmd.sh"]
