"""Pytest-wide safeguards for the shared development database."""

import os


# Tests import the package-level compatibility application.  Select its
# in-memory configuration before any test module imports ``app`` so cleanup
# fixtures can never drop tables from app/propwise.db.
os.environ.setdefault("PROPWISE_TESTING", "1")
