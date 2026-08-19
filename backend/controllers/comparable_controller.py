from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from backend.extensions import db
from backend.models import Activity
from backend.services.activity_service import record_activity
from backend.services.valuation_service import find_comparables, property_from_payload

comparable_bp = Blueprint("comparable_api", __name__, url_prefix="/api/comparables")


@comparable_bp.post("/search")
@login_required
def search():
    data = request.get_json(silent=True) or request.form
    property_data = property_from_payload(data, area_default=1500)
    comps = find_comparables(property_data)
    record_activity(db, Activity, current_user.id, "comparable_search_api", "API comparable search")
    db.session.commit()
    return jsonify({"comparables": comps})
