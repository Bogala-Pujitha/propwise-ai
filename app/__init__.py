import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BASE_DIR))

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

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "propwise-ai-secret-key-2024"
)

database_url = os.environ.get("DATABASE_URL")
if database_url:
    if database_url.startswith("postgres://"):
        database_url = (
            "postgresql+psycopg2://" + database_url[len("postgres://"):]
        )
    elif database_url.startswith("postgresql://"):
        database_url = (
            "postgresql+psycopg2://" + database_url[len("postgresql://"):]
        )
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    configure_database(app)
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"sqlite:///{os.path.join(BASE_DIR, 'propwise.db')}"
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
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
    Create database tables.

    Uses the configured database (SQLite by default,
    PostgreSQL when DATABASE_URL is provided).
    """
    with app.app_context():
        db.create_all()


# ---------------------------------------------------------
# ML ENGINE INITIALIZATION
# ---------------------------------------------------------

def init_engine():
    global VALUATION_ENGINE, MASTER_DF, DROPDOWN_DATA

    if VALUATION_ENGINE is not None and DROPDOWN_DATA is not None:
        return

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

    try:
        VALUATION_ENGINE = ValuationEngine(
            models_dir,
            MASTER_DF,
        )
    except Exception:
        VALUATION_ENGINE = None

    try:
        DROPDOWN_DATA = get_all_dropdown_data(
            MASTER_DF,
        )
    except Exception:
        DROPDOWN_DATA = {}


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

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required", "error")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
            return render_template("register.html")

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(
            username=username,
            email=email,
            password_hash=pw_hash,
            role="user",
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            session.permanent = True
            session["login_time"] = datetime.utcnow().isoformat()
            log_activity(user.id, "login", "User logged in")
            db.session.commit()

            if role == "admin" and user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))

        flash("Invalid credentials", "error")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    log_activity(current_user.id, "logout", "User logged out")
    db.session.commit()
    logout_user()
    return redirect(url_for("landing"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.query.filter_by(email=email).first()
        if user:
            flash(
                "Password reset link sent to your email (demo - not implemented)",
                "success",
            )
        else:
            flash("Email not found", "error")
    return render_template("forgot_password.html")


@app.route("/api/dropdown-data")
@login_required
def api_dropdown_data():
    global DROPDOWN_DATA
    if DROPDOWN_DATA is None:
        from app.services.geocoding import get_all_dropdown_data

        DROPDOWN_DATA = get_all_dropdown_data(MASTER_DF)
    return jsonify(DROPDOWN_DATA)


@app.route("/dashboard")
@login_required
def dashboard():
    if DROPDOWN_DATA is None:
        init_engine()

    predictions = (
        Prediction.query.filter_by(user_id=current_user.id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )
    total_predictions = (
        Prediction.query.filter_by(user_id=current_user.id).count()
    )
    dropdown_data = DROPDOWN_DATA or {}
    return render_template(
        "dashboard.html",
        predictions=predictions,
        total_predictions=total_predictions,
        dropdown=dropdown_data,
    )


@app.route("/predict", methods=["POST"])
@login_required
def predict():
    data = request.get_json() if request.is_json else request.form

    property_data = {
        "property_type": data.get("property_type", "Apartment"),
        "city": data.get("city", "Hyderabad"),
        "locality": data.get("locality", ""),
        "area_sqft": float(data.get("area_sqft", 0)),
        "bhk": int(data.get("bhk", 2)),
        "bathrooms": int(data.get("bathrooms", 2)),
        "property_age": int(data.get("property_age", 5)),
    }

    if VALUATION_ENGINE is None:
        init_engine()

    result = VALUATION_ENGINE.predict(property_data)

    if "error" in result:
        if request.is_json:
            return jsonify(result), 400
        flash(result["error"], "error")
        return redirect(url_for("dashboard"))

    pred = Prediction(
        user_id=current_user.id,
        property_type=property_data["property_type"],
        city=property_data["city"],
        locality=property_data["locality"],
        area_sqft=property_data["area_sqft"],
        bhk=property_data["bhk"],
        bathrooms=property_data["bathrooms"],
        predicted_price=result["predicted_price"],
        lower_bound=result["uncertainty"]["lower_bound"],
        upper_bound=result["uncertainty"]["upper_bound"],
        reliability=result["reliability"]["level"],
        recommendation=result["fair_listing"]["recommendation"],
        property_data=json.dumps(property_data),
    )
    db.session.add(pred)
    log_activity(
        current_user.id,
        "prediction",
        "Predicted {} in {}: INR {:,.0f}".format(
            property_data["property_type"],
            property_data["city"],
            result["predicted_price"],
        ),
    )
    db.session.commit()

    if request.is_json:
        return jsonify(result)

    return render_template("result.html", result=result, property=property_data)


@app.route("/what-if", methods=["GET", "POST"])
@login_required
def what_if():
    if request.method == "GET":
        return render_template(
            "what_if.html",
            original=None,
            modified=None,
            base_property={},
            changes={},
        )

    data = request.get_json() if request.is_json else request.form
    base = {
        "property_type": data.get("property_type", "Apartment"),
        "city": data.get("city", "Hyderabad"),
        "locality": data.get("locality", ""),
        "area_sqft": float(data.get("area_sqft", 1500)),
        "bhk": int(data.get("bhk", 3)),
        "bathrooms": int(data.get("bathrooms", 2)),
        "property_age": int(data.get("property_age", 5)),
    }
    changes = {}
    if data.get("change_bhk"):
        changes["bhk"] = int(data["change_bhk"])
    if data.get("change_area"):
        changes["area_sqft"] = float(data["change_area"])
    if data.get("change_bathrooms"):
        changes["bathrooms"] = int(data["change_bathrooms"])
    if data.get("change_age"):
        changes["property_age"] = int(data["change_age"])

    if VALUATION_ENGINE is None:
        init_engine()

    original_result = VALUATION_ENGINE.predict(base)
    modified_property = base.copy()
    modified_property.update(changes)
    modified_result = VALUATION_ENGINE.predict(modified_property)

    log_activity(
        current_user.id,
        "what_if",
        "What-If analysis for {} in {}".format(
            base["property_type"], base["city"]
        ),
    )
    db.session.commit()

    if request.is_json:
        return jsonify(
            {
                "original": original_result,
                "modified": modified_result,
                "changes": changes,
            }
        )

    return render_template(
        "what_if.html",
        original=original_result,
        modified=modified_result,
        base_property=base,
        changes=changes,
    )


@app.route("/comparables", methods=["GET", "POST"])
@login_required
def comparables():
    if request.method == "GET":
        return render_template("comparables.html", comparables=[], property={})

    data = request.get_json() if request.is_json else request.form
    property_data = {
        "property_type": data.get("property_type", "Apartment"),
        "city": data.get("city", "Hyderabad"),
        "locality": data.get("locality", ""),
        "area_sqft": float(data.get("area_sqft", 1500)),
    }

    if VALUATION_ENGINE is None:
        init_engine()

    comps = VALUATION_ENGINE.comparable_engine.find_comparables(property_data)

    log_activity(
        current_user.id,
        "comparable_search",
        "Comparables for {} in {}".format(
            property_data["property_type"], property_data["city"]
        ),
    )
    db.session.commit()

    if request.is_json:
        return jsonify({"comparables": comps})

    return render_template("comparables.html", comparables=comps, property=property_data)


@app.route("/bulk-valuation", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_valuation():
    if request.method == "GET":
        return render_template("bulk_valuation.html", results=None)

    if "file" not in request.files:
        flash("No file uploaded", "error")
        return render_template("bulk_valuation.html", results=None)

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return render_template("bulk_valuation.html", results=None)

    if not file.filename.endswith(".csv"):
        flash("Only CSV files are supported", "error")
        return render_template("bulk_valuation.html", results=None)

    try:
        df = pd.read_csv(file)
    except Exception as e:
        flash("Error reading CSV: {}".format(str(e)), "error")
        return render_template("bulk_valuation.html", results=None)

    col_map = {}
    for col in df.columns:
        cl = col.lower().strip()
        if cl in [
            "property_type",
            "type",
            "buildtype",
        ]:
            col_map[col] = "property_type"
        elif cl in [
            "city",
            "location_city",
        ]:
            col_map[col] = "city"
        elif cl in [
            "locality",
            "location",
            "area_name",
            "address",
        ]:
            col_map[col] = "locality"
        elif cl in [
            "area",
            "area_sqft",
            "size",
            "total_area",
            "super area",
        ]:
            col_map[col] = "area_sqft"
        elif cl in [
            "bhk",
            "bedrooms",
            "no. of bedrooms",
            "bedroom",
        ]:
            col_map[col] = "bhk"
        elif cl in [
            "bathrooms",
            "bath",
            "bathroom",
        ]:
            col_map[col] = "bathrooms"
    df = df.rename(columns=col_map)

    if VALUATION_ENGINE is None:
        init_engine()

    results = []
    for idx, row in df.iterrows():
        prop = {
            "property_type": str(row.get("property_type", "Apartment")),
            "city": str(row.get("city", "Hyderabad")),
            "locality": str(row.get("locality", "")),
            "area_sqft": float(row.get("area_sqft", 1000)),
            "bhk": int(row.get("bhk", 2))
            if pd.notna(row.get("bhk"))
            else 2,
            "bathrooms": int(row.get("bathrooms", 2))
            if pd.notna(row.get("bathrooms"))
            else 2,
            "property_age": int(row.get("property_age", 5))
            if pd.notna(row.get("property_age"))
            else 5,
        }
        pred = VALUATION_ENGINE.predict(prop)
        if "error" not in pred:
            results.append(
                {
                    "property_id": idx + 1,
                    "property_type": prop["property_type"],
                    "city": prop["city"],
                    "locality": prop["locality"],
                    "area_sqft": prop["area_sqft"],
                    "bhk": prop["bhk"],
                    "predicted_price": pred["predicted_price"],
                    "lower_bound": pred["uncertainty"]["lower_bound"],
                    "upper_bound": pred["uncertainty"]["upper_bound"],
                    "price_per_sqft": pred["price_per_sqft"],
                    "reliability": pred["reliability"]["level"],
                    "ood_flag": pred["ood"]["is_ood"],
                    "recommendation": pred["fair_listing"][
                        "recommendation"
                    ],
                }
            )

    log_activity(
        current_user.id,
        "bulk_valuation",
        "Bulk valuation of {} properties".format(len(results)),
    )
    db.session.commit()

    return render_template(
        "bulk_valuation.html", results=results, count=len(results)
    )


@app.route("/market-intelligence")
@login_required
def market_intelligence():
    if MASTER_DF is None:
        init_engine()

    city_stats = {}
    if MASTER_DF is not None and len(MASTER_DF) > 0:
        for city in MASTER_DF["city"].unique():
            city_df = MASTER_DF[MASTER_DF["city"] == city]
            city_stats[city] = {
                "total_properties": len(city_df),
                "avg_price": round(city_df["price"].mean(), 2),
                "avg_price_per_sqft": round(
                    city_df["price_per_sqft"].mean(), 2
                )
                if "price_per_sqft" in city_df.columns
                else 0,
                "property_types": city_df["property_type"]
                .value_counts()
                .to_dict(),
                "avg_area": round(city_df["area_sqft"].mean(), 0),
            }

    return render_template("market_intelligence.html", city_stats=city_stats)


@app.route("/map")
@login_required
def map_view():
    return render_template("map.html")


@app.route("/model-performance")
@login_required
def model_performance():
    metadata = {}
    models_dir = os.path.join(BASE_DIR, "..", "models")
    meta_path = os.path.join(models_dir, "all_models_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            metadata = json.load(f)

    return render_template("model_performance.html", metadata=metadata)


@app.route("/experiments")
@login_required
def experiments():
    experiments_data = {}
    models_dir = os.path.join(BASE_DIR, "..", "models")

    experiment_meta = {
        "experiment_a": "Experiment A: Hyderabad Only",
        "experiment_b": "Experiment B: India-Wide",
        "experiment_c": "Experiment C: Hybrid",
    }

    for key in experiment_meta:
        experiments_data[key] = {"label": experiment_meta[key], "models": {}}

    def _normalize_experiment(name):
        if not name:
            return None
        n = str(name).strip().lower()
        if n in ("expa", "experiment_a", "a", "exp_a"):
            return "experiment_a"
        if n in ("expb", "experiment_b", "b", "exp_b"):
            return "experiment_b"
        if n in ("expc", "experiment_c", "c", "exp_c"):
            return "experiment_c"
        return None

    def _ingest_metadata(path):
        try:
            with open(path, encoding="utf-8") as fh:
                meta = json.load(fh)
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(meta, dict):
            return
        exp = _normalize_experiment(
            meta.get("experiment")
            or meta.get("experiment_name")
            or ""
        )
        if exp is None:
            return
        pt = meta.get("property_type") or os.path.basename(path).replace("_metadata.json", "")
        experiments_data[exp]["models"][str(pt)] = meta

    if os.path.isdir(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith("_metadata.json") and filename != "all_models_metadata.json":
                _ingest_metadata(os.path.join(models_dir, filename))

        for exp_name in experiment_meta:
            exp_dir = os.path.join(models_dir, exp_name)
            if os.path.isdir(exp_dir):
                for filename in os.listdir(exp_dir):
                    if filename.endswith("_metadata.json"):
                        _ingest_metadata(os.path.join(exp_dir, filename))

    best_models = {}
    best_path = os.path.join(models_dir, "all_models_metadata.json")
    if os.path.exists(best_path):
        with open(best_path) as f:
            best_models = json.load(f)

    return render_template(
        "experiments.html",
        experiments=experiments_data,
        best_models=best_models,
    )


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    if DROPDOWN_DATA is None:
        init_engine()

    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    recent_activities = (
        Activity.query.order_by(Activity.created_at.desc()).limit(20).all()
    )
    predictions_by_type = db.session.query(
        Prediction.property_type,
        db.func.count(Prediction.id),
    ).group_by(Prediction.property_type).all()
    predictions_by_city = db.session.query(
        Prediction.city,
        db.func.count(Prediction.id),
    ).group_by(Prediction.city).all()
    predictions_by_reliability = db.session.query(
        Prediction.reliability,
        db.func.count(Prediction.id),
    ).group_by(Prediction.reliability).all()

    unique_viewed_users = (
        db.session.query(Prediction.user_id).distinct().count()
    )

    all_predictions = (
        Prediction.query.order_by(Prediction.created_at.desc()).limit(10).all()
    )
    all_predictions_dict = [
        {
            "id": p.id,
            "property_type": p.property_type,
            "city": p.city,
            "locality": p.locality,
            "area_sqft": p.area_sqft,
            "predicted_price": p.predicted_price,
            "reliability": p.reliability,
            "created_at": p.created_at.isoformat()
            if p.created_at
            else None,
        }
        for p in all_predictions
    ]

    dropdown_data = DROPDOWN_DATA or {}

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_predictions=total_predictions,
        unique_viewed_users=unique_viewed_users,
        recent_activities=recent_activities,
        predictions_by_type=predictions_by_type,
        predictions_by_city=predictions_by_city,
        predictions_by_reliability=predictions_by_reliability,
        predictions=all_predictions_dict,
        dropdown=dropdown_data,
    )


@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    user_activity = {}
    for u in users:
        pred_count = Prediction.query.filter_by(user_id=u.id).count()
        act_count = Activity.query.filter_by(user_id=u.id).count()
        user_activity[u.id] = {
            "predictions": pred_count,
            "activities": act_count,
        }
    return render_template("admin_users.html", users=users, user_activity=user_activity)


@app.route("/admin/analytics")
@login_required
@admin_required
def admin_analytics():
    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    total_activities = Activity.query.count()

    recent_predictions = (
        Prediction.query.order_by(Prediction.created_at.desc()).limit(50).all()
    )

    property_views = db.session.query(
        Prediction.property_type,
        db.func.count(Prediction.id),
    ).group_by(Prediction.property_type).all()

    location_views = db.session.query(
        Prediction.city,
        db.func.count(Prediction.id),
    ).group_by(Prediction.city).order_by(
        db.func.count(Prediction.id).desc()
    ).limit(10).all()

    locality_views = db.session.query(
        Prediction.locality,
        db.func.count(Prediction.id),
    ).group_by(Prediction.locality).order_by(
        db.func.count(Prediction.id).desc()
    ).limit(10).all()

    avg_prediction = (
        db.session.query(db.func.avg(Prediction.predicted_price)).scalar() or 0
    )

    return render_template(
        "admin_analytics.html",
        total_users=total_users,
        total_predictions=total_predictions,
        total_activities=total_activities,
        recent_predictions=recent_predictions,
        property_views=property_views,
        location_views=location_views,
        locality_views=locality_views,
        avg_prediction=avg_prediction,
    )


@app.route("/admin/audit")
@login_required
@admin_required
def admin_audit():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    return render_template("admin_audit.html", logs=logs)


# ---------------------------------------------------------
# APPLICATION STARTUP
# ---------------------------------------------------------

if __name__ == "__main__":

    # Initialize database tables
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


# Initialize ML engine when app module is imported
# Disabled to avoid import-time side effects that break test isolation.
# Routes that need the engine call init_engine() on demand.
# try:
#     init_engine()
# except Exception:
#     pass


# ---------------------------------------------------------
# CONTROLLER BLUEPRINTS
# ---------------------------------------------------------

from app.controllers import register_blueprints

register_blueprints(app)