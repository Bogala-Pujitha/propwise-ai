from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Activity
from app.services.activity_service import record_activity
from app.services.valuation_service import api_what_if_properties, predict_property

what_if_bp = Blueprint("what_if_api", __name__, url_prefix="/api/what-if")


@what_if_bp.post("/simulate")
@login_required
def simulate():
    data = request.get_json(silent=True) or request.form
    base, modified = api_what_if_properties(data)
    original = predict_property(base)
    changed = predict_property(modified)
    record_activity(db, Activity, current_user.id, "what_if_api", "API What-if simulation")
    db.session.commit()
    return jsonify({"original": original, "modified": changed, "changes": modified})
