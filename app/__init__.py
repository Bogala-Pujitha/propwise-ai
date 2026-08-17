import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_bcrypt import Bcrypt
from flask_cors import CORS

# PostgreSQL configuration
from app.config.database import configure_database


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))


# ---------------------------------------------------------
# FLASK APPLICATION
# ---------------------------------------------------------

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "views"),
    static_folder=os.path.join(BASE_DIR, "static"),
)


# ---------------------------------------------------------
# APPLICATION CONFIGURATION
# ---------------------------------------------------------

# SECRET_KEY must be provided through environment variables.
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]

# PostgreSQL is the ONLY supported application database.
# No SQLite fallback.
configure_database(app)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


# ---------------------------------------------------------
# EXTENSIONS
# ---------------------------------------------------------

# Keep ONE SQLAlchemy instance for the entire application.
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

CORS(app)


# ---------------------------------------------------------
# DATABASE MODELS
# ---------------------------------------------------------

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
    )

    password_hash = db.Column(
        db.String(128),
        nullable=False,
    )

    role = db.Column(
        db.String(10),
        default="user",
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    predictions = db.relationship(
        "Prediction",
        backref="user",
        lazy=True,
    )

    activities = db.relationship(
        "Activity",
        backref="user",
        lazy=True,
    )


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
    )

    property_type = db.Column(
        db.String(50),
    )

    city = db.Column(
        db.String(100),
    )

    locality = db.Column(
        db.String(200),
    )

    area_sqft = db.Column(
        db.Float,
    )

    bhk = db.Column(
        db.Integer,
    )

    bathrooms = db.Column(
        db.Integer,
    )

    predicted_price = db.Column(
        db.Float,
    )

    lower_bound = db.Column(
        db.Float,
    )

    upper_bound = db.Column(
        db.Float,
    )

    reliability = db.Column(
        db.String(20),
    )

    recommendation = db.Column(
        db.String(50),
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    property_data = db.Column(
        db.Text,
    )


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
    )

    activity_type = db.Column(
        db.String(50),
    )

    details = db.Column(
        db.Text,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    admin_id = db.Column(
        db.Integer,
    )

    action = db.Column(
        db.String(100),
    )

    details = db.Column(
        db.Text,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )


# ---------------------------------------------------------
# LOGIN MANAGER
# ---------------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# ---------------------------------------------------------
# APPLICATION GLOBALS
# ---------------------------------------------------------

VALUATION_ENGINE = None
MASTER_DF = None
DROPDOWN_DATA = None


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

def initialize_database():
    """
    Create database tables in PostgreSQL.

    The database connection is provided by DATABASE_URL.
    No SQLite database is created or used.
    """
    with app.app_context():
        db.create_all()


# ---------------------------------------------------------
# ML ENGINE INITIALIZATION
# ---------------------------------------------------------

def init_engine():
    global VALUATION_ENGINE, MASTER_DF, DROPDOWN_DATA

    from app.services.valuation_engine import ValuationEngine
    from app.services.geocoding import get_all_dropdown_data

    models_dir = os.path.join(
        BASE_DIR,
        "..",
        "models",
    )

    master_path = os.path.join(
        BASE_DIR,
        "..",
        "data",
        "processed",
        "master_dataset.csv",
    )

    if os.path.exists(master_path):
        MASTER_DF = pd.read_csv(master_path)

    VALUATION_ENGINE = ValuationEngine(
        models_dir,
        MASTER_DF,
    )

    DROPDOWN_DATA = get_all_dropdown_data(
        MASTER_DF,
    )


# ---------------------------------------------------------
# ADMIN AUTHORIZATION
# ---------------------------------------------------------

def admin_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if (
            not current_user.is_authenticated
            or current_user.role != "admin"
        ):
            flash(
                "Admin access required",
                "error",
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------
# ACTIVITY LOGGING
# ---------------------------------------------------------

def log_activity(
    user_id,
    activity_type,
    details,
):
    activity = Activity(
        user_id=user_id,
        activity_type=activity_type,
        details=details,
    )

    db.session.add(activity)


# ---------------------------------------------------------
# APPLICATION ROUTES
# ---------------------------------------------------------
#
# Keep your existing routes below this point unchanged.
#
# Examples:
#
# @app.route("/")
# def landing():
#     ...
#
# @app.route("/register", methods=["GET", "POST"])
# def register():
#     ...
#
# @app.route("/login", methods=["GET", "POST"])
# def login():
#     ...
#
# @app.route("/predict", methods=["POST"])
# def predict():
#     ...
#
# etc.
# ---------------------------------------------------------


# ---------------------------------------------------------
# APPLICATION STARTUP
# ---------------------------------------------------------

if __name__ == "__main__":

    # PostgreSQL database initialization
    initialize_database()

    # Create default admin account if it does not exist
    with app.app_context():

        if not User.query.filter_by(
            username="admin"
        ).first():

            pw = bcrypt.generate_password_hash(
                "admin123"
            ).decode("utf-8")

            admin = User(
                username="admin",
                email="admin@propwise.ai",
                password_hash=pw,
                role="admin",
            )

            db.session.add(admin)
            db.session.commit()

            print(
                "Admin user created: "
                "admin / admin123"
            )

    # Load ML engine
    init_engine()

    print(
        "PropWise AI starting on "
        "http://localhost:5000"
    )

    app.run(
        debug=True,
        port=5000,
    )


# ---------------------------------------------------------
# CONTROLLER BLUEPRINTS
# ---------------------------------------------------------

try:

    from app.controllers import register_blueprints

    register_blueprints(app)

except Exception:
    pass