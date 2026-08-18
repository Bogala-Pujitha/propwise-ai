from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Activity

from app.services.activity_service import record_activity

from app.services.valuation_service import (
    predict_property,
    property_from_payload,
)


valuation_bp = Blueprint(
    "valuation_api",
    __name__,
    url_prefix="/api/valuation",
)


@valuation_bp.post("/predict")
@login_required
def predict():

    data = (
        request.get_json(silent=True)
        or request.form
    )

    # ============================================================
    # REQUIRED VALIDATION
    # ============================================================

    locality = str(
        data.get("locality", "") or ""
    ).strip()

    area_raw = str(
        data.get("area_sqft", "") or ""
    ).strip()

    area_valid = False

    if area_raw:

        try:

            area_value = float(
                area_raw
            )

            if area_value > 0:
                area_valid = True

        except (
            TypeError,
            ValueError,
        ):
            area_valid = False

    # BOTH ARE REQUIRED
    if not locality or not area_valid:

        return jsonify(
            {
                "error": (
                    "Please enter locality and area."
                )
            }
        ), 400

    # ============================================================
    # BUILD PROPERTY DATA
    # ============================================================

    property_data = property_from_payload(
        data,
        area_default=0,
    )

    # ============================================================
    # MODEL PREDICTION
    # ============================================================

    result = predict_property(
        property_data
    )

    if "error" in result:

        return jsonify(result), 400

    # ============================================================
    # ACTIVITY LOG
    # ============================================================

    record_activity(
        db,
        Activity,
        current_user.id,
        "prediction_api",
        (
            "API valuation for {} in {}".format(
                property_data["property_type"],
                property_data["city"],
            )
        ),
    )

    db.session.commit()

    return jsonify(result)