"""
Type stubs and annotations for ACCIO Laundry Management System
This file helps with Flask-related type checking issues.
"""

# Flask-Login type extensions
from flask_login import LoginManager as _LoginManager
from typing import Optional

class LoginManager(_LoginManager):
    """Extended LoginManager with proper type annotations"""
    login_view: Optional[str] = None
    
    def init_app(self, app) -> None:
        """Initialize login manager with app"""
        super().init_app(app)

# Re-export commonly used types
from typing import Dict, List, Optional, Union, Any
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

__all__ = ['LoginManager', 'Dict', 'List', 'Optional', 'Union', 'Any', 'Flask', 'SQLAlchemy']
