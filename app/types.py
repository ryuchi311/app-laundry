"""
Type stubs and annotations for ACCIO Laundry Management System
This file helps with Flask-related type checking issues.
"""

from typing import Any, Dict, List, Optional, Union

from flask import Flask
from flask_login import LoginManager as _LoginManager
from flask_sqlalchemy import SQLAlchemy


class LoginManager(_LoginManager):
    """Extended LoginManager with proper type annotations"""

    login_view: Optional[str] = None

    def init_app(self, app) -> None:
        """Initialize login manager with app"""
        super().init_app(app)


__all__ = [
    "LoginManager",
    "Dict",
    "List",
    "Optional",
    "Union",
    "Any",
    "Flask",
    "SQLAlchemy",
]
