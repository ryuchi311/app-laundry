#!/usr/bin/env python3
"""
Google App Engine entry point for Laundry Management System
This file serves as the main entry point for Google Cloud deployment.
"""

import os
from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    # This is used when running locally only
    # When deploying to App Engine, a webserver process such as Gunicorn will serve the app
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
