"""Flask extension instances shared by every application instance.

Extensions are intentionally unbound here.  ``create_app`` binds them to a
specific Flask application, which keeps the web process and the test suite
isolated from one another.
"""

from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
cors = CORS()


@login_manager.user_loader
def load_user(user_id):
    """Resolve Flask-Login users without importing the application package."""
    from app.models.user import User

    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None
