"""Backward-compatible admin model alias.

Administrators are users with ``role == 'admin'``; creating a separate table
would split existing account data, so the alias deliberately shares ``users``.
"""

from .user import User

Admin = User

__all__ = ["Admin"]
