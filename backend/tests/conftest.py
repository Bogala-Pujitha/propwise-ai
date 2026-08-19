"""Pytest-wide safeguards for the shared development database."""

import os


# Tests import the package-level compatibility application.  Select its
# in-memory configuration before any test module imports ``backend`` so cleanup
# fixtures can never drop tables from backend/propwise.db.
os.environ.setdefault("PROPWISE_TESTING", "1")
