"""
Application analytics service for PropWise AI.

Reads the existing Activity, Prediction and User models and returns plain
Python dictionaries suitable for the Admin dashboard or an API response.
"""
from datetime import datetime, timedelta

from sqlalchemy import func

from backend.extensions import db
from backend.models import Activity, Prediction, User


def _models():
    return db, User, Prediction, Activity


def admin_summary(days=30):
    db, User, Prediction, Activity = _models()
    since = datetime.utcnow() - timedelta(days=days)

    total_users = User.query.count()
    active_users = (
        db.session.query(func.count(func.distinct(Activity.user_id)))
        .filter(Activity.created_at >= since)
        .scalar()
        or 0
    )
    total_predictions = Prediction.query.count()
    recent_predictions = (
        Prediction.query.filter(Prediction.created_at >= since).count()
    )

    activity_by_type = (
        db.session.query(
            Activity.activity_type,
            func.count(Activity.id),
        )
        .filter(Activity.created_at >= since)
        .group_by(Activity.activity_type)
        .order_by(func.count(Activity.id).desc())
        .all()
    )

    predictions_by_type = (
        db.session.query(
            Prediction.property_type,
            func.count(Prediction.id),
        )
        .group_by(Prediction.property_type)
        .order_by(func.count(Prediction.id).desc())
        .all()
    )

    predictions_by_city = (
        db.session.query(
            Prediction.city,
            func.count(Prediction.id),
        )
        .group_by(Prediction.city)
        .order_by(func.count(Prediction.id).desc())
        .all()
    )

    return {
        "period_days": days,
        "total_users": total_users,
        "active_users": active_users,
        "total_predictions": total_predictions,
        "recent_predictions": recent_predictions,
        "activity_by_type": [
            {"activity_type": name, "count": count}
            for name, count in activity_by_type
        ],
        "predictions_by_type": [
            {"property_type": name, "count": count}
            for name, count in predictions_by_type
        ],
        "predictions_by_city": [
            {"city": name or "Unknown", "count": count}
            for name, count in predictions_by_city
        ],
    }


def most_active_users(limit=10):
    db, User, _Prediction, Activity = _models()

    rows = (
        db.session.query(
            User.id,
            User.username,
            func.count(Activity.id).label("activity_count"),
        )
        .join(Activity, Activity.user_id == User.id)
        .group_by(User.id, User.username)
        .order_by(func.count(Activity.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "user_id": row.id,
            "username": row.username,
            "activity_count": row.activity_count,
        }
        for row in rows
    ]


def activity_breakdown(limit=20):
    db, _User, _Prediction, Activity = _models()

    rows = (
        db.session.query(
            Activity.activity_type,
            func.count(Activity.id).label("count"),
        )
        .group_by(Activity.activity_type)
        .order_by(func.count(Activity.id).desc())
        .limit(limit)
        .all()
    )

    return [
        {"activity_type": row.activity_type, "count": row.count}
        for row in rows
    ]


def build_user_summary(User, Prediction, Activity, user_id):
    prediction_count = Prediction.query.filter_by(user_id=user_id).count()
    activity_count = Activity.query.filter_by(user_id=user_id).count()
    recent_predictions = (
        Prediction.query.filter_by(user_id=user_id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activities = (
        Activity.query.filter_by(user_id=user_id)
        .order_by(Activity.created_at.desc())
        .limit(10)
        .all()
    )
    return {
        "prediction_count": prediction_count,
        "activity_count": activity_count,
        "recent_predictions": recent_predictions,
        "recent_activities": recent_activities,
    }


def build_admin_summary(db, User, Prediction, Activity):
    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    total_activities = Activity.query.count()
    average_prediction = (
        db.session.query(func.avg(Prediction.predicted_price)).scalar() or 0
    )

    predictions_by_type = (
        db.session.query(
            Prediction.property_type,
            func.count(Prediction.id),
        )
        .group_by(Prediction.property_type)
        .order_by(func.count(Prediction.id).desc())
        .all()
    )

    predictions_by_city = (
        db.session.query(
            Prediction.city,
            func.count(Prediction.id),
        )
        .group_by(Prediction.city)
        .order_by(func.count(Prediction.id).desc())
        .all()
    )

    predictions_by_locality = (
        db.session.query(
            Prediction.locality,
            func.count(Prediction.id),
        )
        .group_by(Prediction.locality)
        .order_by(func.count(Prediction.id).desc())
        .all()
    )

    predictions_by_reliability = (
        db.session.query(
            Prediction.reliability,
            func.count(Prediction.id),
        )
        .group_by(Prediction.reliability)
        .order_by(func.count(Prediction.id).desc())
        .all()
    )

    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "total_activities": total_activities,
        "average_prediction": average_prediction,
        "predictions_by_type": [
            {"property_type": name or "Unknown", "count": count}
            for name, count in predictions_by_type
        ],
        "predictions_by_city": [
            {"city": name or "Unknown", "count": count}
            for name, count in predictions_by_city
        ],
        "predictions_by_locality": [
            {"locality": name or "Unknown", "count": count}
            for name, count in predictions_by_locality
        ],
        "predictions_by_reliability": [
            {"reliability": name or "Unknown", "count": count}
            for name, count in predictions_by_reliability
        ],
    }
