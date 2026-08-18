from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Activity
from app.services.activity_service import record_activity
from app.services.valuation_service import predict_property, property_from_payload

valuation_bp = Blueprint("valuation_api", __name__, url_prefix="/api/valuation")


@valuation_bp.post("/predict")
@login_required
def predict():
    data = request.get_json(silent=True) or request.form
    property_data = property_from_payload(data, area_default=0)
    result = predict_property(property_data)
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
