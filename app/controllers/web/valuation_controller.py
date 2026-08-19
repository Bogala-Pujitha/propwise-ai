"""Browser valuation workflow controller."""

import pandas as pd

from flask import (
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app.security import admin_required

from app.extensions import db

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
    """Run a single-property valuation."""

    data = (
        request.get_json(silent=True)
        if request.is_json
        else request.form
    )

    # ------------------------------------------------------------
    # REQUIRED VALIDATION
    # Locality and area are mandatory.
    # ------------------------------------------------------------

    locality = str(
        data.get("locality", "") or ""
    ).strip()

    area_raw = str(
        data.get("area_sqft", "") or ""
    ).strip()

    area_valid = False

    if area_raw:
        try:
            area_value = float(area_raw)

            if area_value > 0:
                area_valid = True

        except (TypeError, ValueError):
            area_valid = False

    if not locality or not area_valid:

        error_message = (
            "Please enter locality and area."
        )

        if request.is_json:
            return jsonify(
                {
                    "error": error_message
                }
            ), 400

        flash(error_message, "error")

        return redirect(
            url_for("dashboard")
        )

    # ------------------------------------------------------------
    # BUILD PROPERTY DATA
    # ------------------------------------------------------------

    property_data = property_from_payload(
        data,
        area_default=0,
    )

    # ------------------------------------------------------------
    # RUN PREDICTION
    # ------------------------------------------------------------

    result = predict_property(
        property_data
    )

    if "error" in result:

        if request.is_json:
            return jsonify(result), 400

        flash(
            result["error"],
            "error",
        )

        return redirect(
            url_for("dashboard")
        )

    # ------------------------------------------------------------
    # SAVE PREDICTION
    # ------------------------------------------------------------

    save_prediction(
        db,
        user_id=current_user.id,
        property_data=property_data,
        result=result,
    )

    # ------------------------------------------------------------
    # ACTIVITY LOG
    # ------------------------------------------------------------

    record_activity(
        user_id=current_user.id,
        activity_type="prediction",
        details=(
            "Predicted {} in {}: INR {:,.0f}".format(
                property_data["property_type"],
                property_data["city"],
                result["predicted_price"],
            )
        ),
        commit=False,
    )

    db.session.commit()

    # ------------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------------

    if request.is_json:
        return jsonify(result)

    return render_template(
        "result.html",
        result=result,
        property=property_data,
    )


@login_required
def what_if():
    """Run what-if valuation analysis."""

    if request.method == "GET":

        return render_template(
            "what_if.html",
            original=None,
            modified=None,
            base_property={},
            changes={},
        )

    data = (
        request.get_json(silent=True)
        if request.is_json
        else request.form
    )

    (
        base_property,
        modified_property,
        changes,
    ) = what_if_properties(data)

    original_result = predict_property(
        base_property
    )

    modified_result = predict_property(
        modified_property
    )

    record_activity(
        user_id=current_user.id,
        activity_type="what_if",
        details=(
            "What-If analysis for {} in {}".format(
                base_property["property_type"],
                base_property["city"],
            )
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
    """Find comparable properties."""

    if request.method == "GET":

        return render_template(
            "comparables.html",
            comparables=[],
            property={},
        )

    data = (
        request.get_json(silent=True)
        if request.is_json
        else request.form
    )

    property_data = property_from_payload(
        data,
        area_default=1500,
    )

    comparables_result = find_comparables(
        property_data
    )

    record_activity(
        user_id=current_user.id,
        activity_type="comparable_search",
        details=(
            "Comparables for {} in {}".format(
                property_data["property_type"],
                property_data["city"],
            )
        ),
        commit=False,
    )

    db.session.commit()

    if request.is_json:

        return jsonify(
            {
                "comparables": comparables_result
            }
        )

    return render_template(
        "comparables.html",
        comparables=comparables_result,
        property=property_data,
    )


@login_required
@admin_required
def bulk_valuation():
    """Run bulk CSV valuation.

    Both normal authenticated users and admins can access
    this endpoint.

    IMPORTANT:
    There is intentionally NO @admin_required decorator.
    """

    if request.method == "GET":

        return render_template(
            "bulk_valuation.html",
            results=None,
        )

    # ------------------------------------------------------------
    # ACCEPT BOTH FILE FIELD NAMES
    # ------------------------------------------------------------

    file = request.files.get("file")

    if file is None:
        file = request.files.get("csv_file")

    if file is None:

        flash(
            "No file uploaded",
            "error",
        )

        return render_template(
            "bulk_valuation.html",
            results=None,
        )

    if file.filename == "":

        flash(
            "No file selected",
            "error",
        )

        return render_template(
            "bulk_valuation.html",
            results=None,
        )

    if not file.filename.lower().endswith(".csv"):

        flash(
            "Only CSV files are supported",
            "error",
        )

        return render_template(
            "bulk_valuation.html",
            results=None,
        )

    # ------------------------------------------------------------
    # READ CSV
    # ------------------------------------------------------------

    try:

        dataframe = pd.read_csv(file)

    except Exception as error:

        flash(
            "Error reading CSV: {}".format(
                str(error)
            ),
            "error",
        )

        return render_template(
            "bulk_valuation.html",
            results=None,
        )

    # ------------------------------------------------------------
    # RUN BULK VALUATION
    # ------------------------------------------------------------

    try:

        results = bulk_valuate(
            dataframe
        )

    except Exception as error:

        flash(
            "Error during bulk valuation: {}".format(
                str(error)
            ),
            "error",
        )

        return render_template(
            "bulk_valuation.html",
            results=None,
        )

    # ------------------------------------------------------------
    # ACTIVITY LOG
    # ------------------------------------------------------------

    record_activity(
        user_id=current_user.id,
        activity_type="bulk_valuation",
        details=(
            "Bulk valuation of {} properties".format(
                len(results)
            )
        ),
        commit=False,
    )

    db.session.commit()

    # ------------------------------------------------------------
    # RESULT
    # ------------------------------------------------------------

    return render_template(
        "bulk_valuation.html",
        results=results,
        count=len(results),
    )