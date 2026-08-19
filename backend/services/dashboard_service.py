"""Read models and datasets for the HTML dashboard controllers."""

from __future__ import annotations

import json
from pathlib import Path

from backend.extensions import db
from backend.models import Activity, AuditLog, Prediction, User


def user_dashboard_context(user_id: int, dropdown_data: dict | None) -> dict:
    predictions = (
        Prediction.query.filter_by(user_id=user_id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )
    return {
        "predictions": predictions,
        "total_predictions": Prediction.query.filter_by(user_id=user_id).count(),
        "dropdown": dropdown_data or {},
    }


def market_intelligence(master_df) -> dict:
    city_stats = {}
    if master_df is not None and len(master_df) > 0:
        for city in master_df["city"].unique():
            city_df = master_df[master_df["city"] == city]
            city_stats[city] = {
                "total_properties": len(city_df),
                "avg_price": round(city_df["price"].mean(), 2),
                "avg_price_per_sqft": round(
                    city_df["price_per_sqft"].mean(), 2
                )
                if "price_per_sqft" in city_df.columns
                else 0,
                "property_types": city_df["property_type"].value_counts().to_dict(),
                "avg_area": round(city_df["area_sqft"].mean(), 0),
            }
    return city_stats


def model_metadata(models_dir: str | Path) -> dict:
    path = Path(models_dir) / "all_models_metadata.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def experiments_context(models_dir: str | Path) -> tuple[dict, dict]:
    """Return the exact template contract of the legacy experiments route."""
    models_path = Path(models_dir)
    experiment_labels = {
        "experiment_a": "Experiment A: Hyderabad Only",
        "experiment_b": "Experiment B: India-Wide",
        "experiment_c": "Experiment C: Hybrid",
    }
    experiments = {
        key: {"label": label, "models": {}}
        for key, label in experiment_labels.items()
    }

    def normalize_experiment(name):
        if not name:
            return None
        value = str(name).strip().lower()
        aliases = {
            "expa": "experiment_a",
            "experiment_a": "experiment_a",
            "a": "experiment_a",
            "exp_a": "experiment_a",
            "expb": "experiment_b",
            "experiment_b": "experiment_b",
            "b": "experiment_b",
            "exp_b": "experiment_b",
            "expc": "experiment_c",
            "experiment_c": "experiment_c",
            "c": "experiment_c",
            "exp_c": "experiment_c",
        }
        return aliases.get(value)

    def ingest_metadata(path: Path):
        try:
            with path.open(encoding="utf-8") as handle:
                metadata = json.load(handle)
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(metadata, dict):
            return
        experiment = normalize_experiment(
            metadata.get("experiment") or metadata.get("experiment_name") or ""
        )
        if experiment is None:
            return
        property_type = metadata.get("property_type") or path.name.replace(
            "_metadata.json", ""
        )
        experiments[experiment]["models"][str(property_type)] = metadata

    if models_path.is_dir():
        for path in models_path.glob("*_metadata.json"):
            if path.name != "all_models_metadata.json":
                ingest_metadata(path)
        for experiment_name in experiment_labels:
            experiment_dir = models_path / experiment_name
            if experiment_dir.is_dir():
                for path in experiment_dir.glob("*_metadata.json"):
                    ingest_metadata(path)

    return experiments, model_metadata(models_path)


def admin_dashboard_context(dropdown_data: dict | None) -> dict:
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
    predictions = (
        Prediction.query.order_by(Prediction.created_at.desc()).limit(10).all()
    )

    return {
        "total_users": User.query.count(),
        "total_predictions": Prediction.query.count(),
        "unique_viewed_users": db.session.query(Prediction.user_id)
        .distinct()
        .count(),
        "recent_activities": Activity.query.order_by(Activity.created_at.desc())
        .limit(20)
        .all(),
        "predictions_by_type": predictions_by_type,
        "predictions_by_city": predictions_by_city,
        "predictions_by_reliability": predictions_by_reliability,
        "predictions": [
            {
                "id": prediction.id,
                "property_type": prediction.property_type,
                "city": prediction.city,
                "locality": prediction.locality,
                "area_sqft": prediction.area_sqft,
                "predicted_price": prediction.predicted_price,
                "reliability": prediction.reliability,
                "created_at": prediction.created_at.isoformat()
                if prediction.created_at
                else None,
            }
            for prediction in predictions
        ],
        "dropdown": dropdown_data or {},
    }


def admin_users_context() -> dict:
    users = User.query.all()
    user_activity = {}
    for user in users:
        user_activity[user.id] = {
            "predictions": Prediction.query.filter_by(user_id=user.id).count(),
            "activities": Activity.query.filter_by(user_id=user.id).count(),
        }
    return {"users": users, "user_activity": user_activity}


def admin_analytics_context() -> dict:
    return {
        "total_users": User.query.count(),
        "total_predictions": Prediction.query.count(),
        "total_activities": Activity.query.count(),
        "recent_predictions": Prediction.query.order_by(Prediction.created_at.desc())
        .limit(50)
        .all(),
        "property_views": db.session.query(
            Prediction.property_type,
            db.func.count(Prediction.id),
        ).group_by(Prediction.property_type).all(),
        "location_views": db.session.query(
            Prediction.city,
            db.func.count(Prediction.id),
        )
        .group_by(Prediction.city)
        .order_by(db.func.count(Prediction.id).desc())
        .limit(10)
        .all(),
        "locality_views": db.session.query(
            Prediction.locality,
            db.func.count(Prediction.id),
        )
        .group_by(Prediction.locality)
        .order_by(db.func.count(Prediction.id).desc())
        .limit(10)
        .all(),
        "avg_prediction": db.session.query(
            db.func.avg(Prediction.predicted_price)
        ).scalar()
        or 0,
    }


def recent_audit_logs(limit: int = 50):
    return AuditLog.query.order_by(AuditLog.created_at.desc()).limit(limit).all()
