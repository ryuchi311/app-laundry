This is a minimal Alembic scaffolding to manage database migrations.

Usage:

- Install Alembic (it's already in requirements.txt).
- Edit `alembic.ini` sqlalchemy.url or run migrations using your app's config.
- To create a new revision:
  alembic revision -m "create users table" --autogenerate
- To apply migrations:
  alembic upgrade head

This env.py attempts to import the Flask app factory `create_app` and use
the app's SQLALCHEMY_DATABASE_URI and models metadata if available.
