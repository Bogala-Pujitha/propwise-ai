from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.services.activity_service import record_activity

what_if_bp = Blueprint("what_if_api", __name__, url_prefix="/api/what-if")


@what_if_bp.post("/simulate")
@login_required
def simulate():
    from app import db, init_engine, VALUATION_ENGINE, Activity

    data = request.get_json(silent=True) or request.form
    base = {
        "property_type": data.get("property_type", "Apartment"),
        "city": data.get("city", "Hyderabad"),
        "locality": data.get("locality", ""),
        "area_sqft": float(data.get("area_sqft", 1500)),
        "bhk": int(data.get("bhk", 3)),
        "bathrooms": int(data.get("bathrooms", 2)),
        "property_age": int(data.get("property_age", 5)),
    }
    modified = dict(base)
    for field in ("bhk", "bathrooms", "property_age"):
        if data.get(field) is not None and data.get(field) != "":
            modified[field] = int(data[field])
    if data.get("area_sqft_modified") not in (None, ""):
        modified["area_sqft"] = float(data["area_sqft_modified"])

    if VALUATION_ENGINE is None:
        init_engine()
        from app import VALUATION_ENGINE as engine
    else:
        engine = VALUATION_ENGINE

    original = engine.predict(base)
    changed = engine.predict(modified)
    record_activity(db, Activity, current_user.id, "what_if_api", "API What-if simulation")
    db.session.commit()
    return jsonify({"original": original, "modified": changed, "changes": modified})
