from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.services.activity_service import record_activity

valuation_bp = Blueprint("valuation_api", __name__, url_prefix="/api/valuation")


@valuation_bp.post("/predict")
@login_required
def predict():
    from app import db, init_engine, VALUATION_ENGINE, Activity

    data = request.get_json(silent=True) or request.form
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
        from app import VALUATION_ENGINE as engine
    else:
        engine = VALUATION_ENGINE

    result = engine.predict(property_data)
    if "error" in result:
        return jsonify(result), 400

    record_activity(
        db,
        Activity,
        current_user.id,
        "prediction_api",
        f"API valuation for {property_data['property_type']} in {property_data['city']}",
    )
    db.session.commit()
    return jsonify(result)
