"""Compatibility imports for code using the former monolithic model module."""

from app.extensions import db
from .activity import Activity
from .audit import AuditLog
from .prediction import Prediction
from .user import User

Admin = User

__all__ = ["db", "User", "Prediction", "Activity", "AuditLog", "Admin"]
