"""Browser valuation workflow controller."""

import pandas as pd
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.security import admin_required
from app.services.activity_service import record_activity
from app.services.valuation_service import (
    bulk_valuate,
    find_comparables,
    predict_property,
    property_from_payload,
    save_prediction,
    what_if_properties,
)


@login_required
def predict():
    data = request.get_json() if request.is_json else request.form
    property_data = property_from_payload(data, area_default=0)
    result = predict_property(property_data)

    if "error" in result:
        if request.is_json:
            return jsonify(result), 400
        flash(result["error"], "error")
        return redirect(url_for("dashboard"))

    save_prediction(
        db,
        user_id=current_user.id,
        property_data=property_data,
        result=result,
    )
    record_activity(
        user_id=current_user.id,
        activity_type="prediction",
        details="Predicted {} in {}: INR {:,.0f}".format(
            property_data["property_type"],
            property_data["city"],
            result["predicted_price"],
        ),
        commit=False,
    )
    db.session.commit()

    if request.is_json:
        return jsonify(result)

    return render_template("result.html", result=result, property=property_data)


@login_required
def what_if():
    if request.method == "GET":
        return render_template(
            "what_if.html",
            original=None,
            modified=None,
            base_property={},
            changes={},
        )

    data = request.get_json() if request.is_json else request.form
    base_property, modified_property, changes = what_if_properties(data)
    original_result = predict_property(base_property)
    modified_result = predict_property(modified_property)

    record_activity(
        user_id=current_user.id,
        activity_type="what_if",
        details="What-If analysis for {} in {}".format(
            base_property["property_type"], base_property["city"]
        ),
        commit=False,
    )
    db.session.commit()

    if request.is_json:
        return jsonify(
            {
                "original": original_result,
                "modified": modified_result,
                "changes": changes,
            }
        )

    return render_template(
        "what_if.html",
        original=original_result,
        modified=modified_result,
        base_property=base_property,
        changes=changes,
    )


@login_required
def comparables():
    if request.method == "GET":
        return render_template("comparables.html", comparables=[], property={})

    data = request.get_json() if request.is_json else request.form
    property_data = property_from_payload(data, area_default=1500)
    comparables_result = find_comparables(property_data)

    record_activity(
        user_id=current_user.id,
        activity_type="comparable_search",
        details="Comparables for {} in {}".format(
            property_data["property_type"], property_data["city"]
        ),
        commit=False,
    )
    db.session.commit()

    if request.is_json:
        return jsonify({"comparables": comparables_result})

    return render_template(
        "comparables.html",
        comparables=comparables_result,
        property=property_data,
    )


@login_required
@admin_required
def bulk_valuation():
    if request.method == "GET":
        return render_template("bulk_valuation.html", results=None)

    if "file" not in request.files:
        flash("No file uploaded", "error")
        return render_template("bulk_valuation.html", results=None)

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected", "error")
        return render_template("bulk_valuation.html", results=None)

    if not file.filename.endswith(".csv"):
        flash("Only CSV files are supported", "error")
        return render_template("bulk_valuation.html", results=None)

    try:
        dataframe = pd.read_csv(file)
    except Exception as error:
        flash("Error reading CSV: {}".format(str(error)), "error")
        return render_template("bulk_valuation.html", results=None)

    results = bulk_valuate(dataframe)
    record_activity(
        user_id=current_user.id,
        activity_type="bulk_valuation",
        details="Bulk valuation of {} properties".format(len(results)),
        commit=False,
    )
    db.session.commit()
    return render_template(
        "bulk_valuation.html", results=results, count=len(results)
    )
