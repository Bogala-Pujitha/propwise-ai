"""Read-only analytics service for the admin dashboard and APIs."""


def build_admin_summary(db, User, Prediction, Activity):
    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    total_activities = Activity.query.count()

    predictions_by_type = db.session.query(
        Prediction.property_type, db.func.count(Prediction.id)
    ).group_by(Prediction.property_type).all()

    predictions_by_city = db.session.query(
        Prediction.city, db.func.count(Prediction.id)
    ).group_by(Prediction.city).order_by(db.func.count(Prediction.id).desc()).all()

    predictions_by_locality = db.session.query(
        Prediction.locality, db.func.count(Prediction.id)
    ).group_by(Prediction.locality).order_by(db.func.count(Prediction.id).desc()).limit(20).all()

    predictions_by_reliability = db.session.query(
        Prediction.reliability, db.func.count(Prediction.id)
    ).group_by(Prediction.reliability).all()

    avg_prediction = db.session.query(db.func.avg(Prediction.predicted_price)).scalar() or 0

    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "total_activities": total_activities,
        "average_prediction": float(avg_prediction),
        "predictions_by_type": predictions_by_type,
        "predictions_by_city": predictions_by_city,
        "predictions_by_locality": predictions_by_locality,
        "predictions_by_reliability": predictions_by_reliability,
    }


def build_user_summary(User, Prediction, Activity, user_id: int):
    predictions = Prediction.query.filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).all()
    activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.created_at.desc()).all()
    return {
        "prediction_count": len(predictions),
        "activity_count": len(activities),
        "recent_predictions": predictions[:10],
        "recent_activities": activities[:20],
    }
