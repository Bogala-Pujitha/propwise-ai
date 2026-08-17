from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.services.activity_service import record_activity

comparable_bp = Blueprint("comparable_api", __name__, url_prefix="/api/comparables")


@comparable_bp.post("/search")
@login_required
def search():
    from app import db, init_engine, VALUATION_ENGINE, Activity

    data = request.get_json(silent=True) or request.form
    property_data = {
        "property_type": data.get("property_type", "Apartment"),
        "city": data.get("city", "Hyderabad"),
        "locality": data.get("locality", ""),
        "area_sqft": float(data.get("area_sqft", 1500)),
    }
    if VALUATION_ENGINE is None:
        init_engine()
        from app import VALUATION_ENGINE as engine
    else:
        engine = VALUATION_ENGINE

    comps = engine.comparable_engine.find_comparables(property_data)
    record_activity(db, Activity, current_user.id, "comparable_search_api", "API comparable search")
    db.session.commit()
    return jsonify({"comparables": comps})
