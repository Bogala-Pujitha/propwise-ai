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

from backend.security import admin_required
from backend.extensions import db
from backend.services.activity_service import record_activity
from backend.services.valuation_service import (
    bulk_valuate,
    find_comparables,
    predict_property,
    property_from_payload,
    save_prediction,
    what_if_properties,
)


# ============================================================
# VALIDATION HELPER
# ============================================================

def validate_prediction_payload(data):
    """
    Validate required fields before the valuation model is called.

    Returns:
        None
            When every required field is valid.

        str
            A user-friendly validation message when one or more
            required fields are missing/invalid.
    """

    data = data or {}

    # --------------------------------------------------------
    # REQUIRED TEXT FIELDS
    # --------------------------------------------------------

    property_type = str(
        data.get("property_type", "") or ""
    ).strip()

    city = str(
        data.get("city", "") or ""
    ).strip()

    locality = str(
        data.get("locality", "") or ""
    ).strip()


    # --------------------------------------------------------
    # REQUIRED NUMERIC FIELDS
    # --------------------------------------------------------

    area_raw = str(
        data.get("area_sqft", "") or ""
    ).strip()

    bhk_raw = str(
        data.get("bhk", "") or ""
    ).strip()

    bathrooms_raw = str(
        data.get("bathrooms", "") or ""
    ).strip()

    age_raw = str(
        data.get("property_age", "") or ""
    ).strip()


    missing_fields = []


    # --------------------------------------------------------
    # PROPERTY TYPE
    # --------------------------------------------------------

    if not property_type:
        missing_fields.append("property type")


    # --------------------------------------------------------
    # CITY
    # --------------------------------------------------------

    if not city:
        missing_fields.append("city")


    # --------------------------------------------------------
    # LOCALITY
    # --------------------------------------------------------

    if not locality:
        missing_fields.append("locality")


    # --------------------------------------------------------
    # AREA
    # --------------------------------------------------------

    try:

        area_value = float(area_raw)

        if area_value <= 0:
            raise ValueError

    except (TypeError, ValueError):

        missing_fields.append("area")


    # --------------------------------------------------------
    # BHK
    # --------------------------------------------------------

    try:

        bhk_value = int(bhk_raw)

        if bhk_value < 0:
            raise ValueError

    except (TypeError, ValueError):

        missing_fields.append("BHK")


    # --------------------------------------------------------
    # BATHROOMS
    # --------------------------------------------------------

    try:

        bathrooms_value = int(bathrooms_raw)

        if bathrooms_value < 0:
            raise ValueError

    except (TypeError, ValueError):

        missing_fields.append("bathrooms")


    # --------------------------------------------------------
    # PROPERTY AGE
    # --------------------------------------------------------

    try:

        age_value = int(age_raw)

        if age_value < 0:
            raise ValueError

    except (TypeError, ValueError):

        missing_fields.append("property age")


    # --------------------------------------------------------
    # EVERYTHING VALID
    # --------------------------------------------------------

    if not missing_fields:
        return None


    # --------------------------------------------------------
    # BUILD USER-FRIENDLY MESSAGE
    # --------------------------------------------------------

    if len(missing_fields) == 1:

        return (
            "Please enter "
            + missing_fields[0]
            + "."
        )


    return (
        "Please enter "
        + ", ".join(
            missing_fields[:-1]
        )
        + " and "
        + missing_fields[-1]
        + "."
    )


# ============================================================
# SINGLE PROPERTY VALUATION
# ============================================================

@login_required
def predict():
    """Run a single-property valuation."""

    data = (
        request.get_json(silent=True)
        if request.is_json
        else request.form
    )


    # --------------------------------------------------------
    # REQUIRED BACKEND VALIDATION
    #
    # IMPORTANT:
    # This happens BEFORE property_from_payload()
    # and BEFORE predict_property().
    #
    # Therefore missing values cannot be replaced by
    # fallback/default values and sent to the ML model.
    # --------------------------------------------------------

    validation_error = (
        validate_prediction_payload(
            data
        )
    )


    if validation_error:

        if request.is_json:

            return jsonify(
                {
                    "error":
                        validation_error
                }
            ), 400


        flash(
            validation_error,
            "error",
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------------
    # BUILD PROPERTY DATA
    # --------------------------------------------------------

    property_data = property_from_payload(
        data,
        area_default=0,
    )


    # --------------------------------------------------------
    # RUN PREDICTION
    # --------------------------------------------------------

    result = predict_property(
        property_data
    )


    if "error" in result:

        if request.is_json:

            return jsonify(
                result
            ), 400


        flash(
            result["error"],
            "error",
        )

        return redirect(
            url_for("dashboard")
        )


    # --------------------------------------------------------
    # SAVE PREDICTION
    # --------------------------------------------------------

    save_prediction(
        db,
        user_id=current_user.id,
        property_data=property_data,
        result=result,
    )


    # --------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    if request.is_json:

        return jsonify(
            result
        )


    return render_template(
        "result.html",
        result=result,
        property=property_data,
    )


# ============================================================
# WHAT-IF ANALYSIS
# ============================================================
# ============================================================
# WHAT-IF ANALYSIS
# ============================================================

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


    try:

        (
            base_property,
            modified_property,
            changes,
        ) = what_if_properties(
            data
        )


        # ----------------------------------------------------
        # ORIGINAL PROPERTY
        # ----------------------------------------------------

        original_result = predict_property(
            base_property
        )


        if (
            isinstance(
                original_result,
                dict
            )
            and "error" in original_result
        ):

            if request.is_json:

                return jsonify(
                    {
                        "error":
                            original_result["error"]
                    }
                ), 400

            flash(
                original_result["error"],
                "error",
            )

            return render_template(
                "what_if.html",
                original=None,
                modified=None,
                base_property=base_property,
                changes=changes,
            )


        # ----------------------------------------------------
        # MODIFIED PROPERTY
        # ----------------------------------------------------

        modified_result = predict_property(
            modified_property
        )


        if (
            isinstance(
                modified_result,
                dict
            )
            and "error" in modified_result
        ):

            if request.is_json:

                return jsonify(
                    {
                        "error":
                            modified_result["error"]
                    }
                ), 400

            flash(
                modified_result["error"],
                "error",
            )

            return render_template(
                "what_if.html",
                original=original_result,
                modified=None,
                base_property=base_property,
                changes=changes,
            )


        # ----------------------------------------------------
        # ACTIVITY LOG
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # JSON RESPONSE
        # Keep the existing output structure unchanged.
        # ----------------------------------------------------

        if request.is_json:

            return jsonify(
                {
                    "original":
                        original_result,

                    "modified":
                        modified_result,

                    "changes":
                        changes,
                }
            )


        # ----------------------------------------------------
        # NORMAL TEMPLATE RESPONSE
        # ----------------------------------------------------

        return render_template(
            "what_if.html",
            original=original_result,
            modified=modified_result,
            base_property=base_property,
            changes=changes,
        )


    except Exception as error:

        # ----------------------------------------------------
        # NEVER HIDE THE REAL ERROR
        # ----------------------------------------------------

        error_message = str(
            error
        )


        print(
            "[WHAT-IF ERROR]",
            error_message
        )


        if request.is_json:

            return jsonify(
                {
                    "error":
                        "What-If analysis failed: "
                        + error_message
                }
            ), 500


        flash(
            "What-If analysis failed: "
            + error_message,
            "error",
        )


        return render_template(
            "what_if.html",
            original=None,
            modified=None,
            base_property={},
            changes={},
        )

# ============================================================
# COMPARABLE PROPERTIES
# ============================================================

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
                "comparables":
                    comparables_result
            }
        )


    return render_template(
        "comparables.html",
        comparables=comparables_result,
        property=property_data,
    )


# ============================================================
# BULK VALUATION
# ============================================================

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


    # --------------------------------------------------------
    # ACCEPT BOTH FILE FIELD NAMES
    # --------------------------------------------------------

    file = request.files.get(
        "file"
    )


    if file is None:

        file = request.files.get(
            "csv_file"
        )


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


    if not file.filename.lower().endswith(
        ".csv"
    ):

        flash(
            "Only CSV files are supported",
            "error",
        )

        return render_template(
            "bulk_valuation.html",
            results=None,
        )


    # --------------------------------------------------------
    # READ CSV
    # --------------------------------------------------------

    try:

        dataframe = pd.read_csv(
            file
        )

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


    # --------------------------------------------------------
    # RUN BULK VALUATION
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return render_template(
        "bulk_valuation.html",
        results=results,
        count=len(results),
    )