"""Business operations shared by browser and JSON valuation controllers."""

from __future__ import annotations

import json

import pandas as pd

from app.models.prediction import Prediction
from app.runtime import get_runtime


def property_from_payload(
    data,
    *,
    area_default: float,
    bhk_default: int = 2,
    bathrooms_default: int = 2,
    age_default: int = 5,
) -> dict:
    """Normalize the established valuation form/API fields into one contract."""
    return {
        "property_type": data.get("property_type", "Apartment"),
        "city": data.get("city", "Hyderabad"),
        "locality": data.get("locality", ""),
        "area_sqft": float(data.get("area_sqft", area_default)),
        "bhk": int(data.get("bhk", bhk_default)),
        "bathrooms": int(data.get("bathrooms", bathrooms_default)),
        "property_age": int(data.get("property_age", age_default)),
        "furnishing": data.get("furnishing", ""),
        "facing": data.get("facing", ""),
        "floor": int(data.get("floor") or 0),
        "total_floors": int(data.get("total_floors") or 0),
        "parking": data.get("parking", ""),
    }


def get_engine():
    """Load and return the app-scoped engine only when a feature needs it."""
    runtime = get_runtime().initialize()
    if runtime.valuation_engine is None:
        raise RuntimeError("Valuation engine is unavailable")
    return runtime.valuation_engine


def predict_property(property_data: dict) -> dict:
    return get_engine().predict(property_data)


def find_comparables(property_data: dict) -> list:
    return get_engine().comparable_engine.find_comparables(property_data)


def save_prediction(db, *, user_id: int, property_data: dict, result: dict) -> Prediction:
    """Persist a prediction using the existing database schema unchanged."""
    prediction = Prediction(
        user_id=user_id,
        property_type=property_data["property_type"],
        city=property_data["city"],
        locality=property_data["locality"],
        area_sqft=property_data["area_sqft"],
        bhk=property_data["bhk"],
        bathrooms=property_data["bathrooms"],
        predicted_price=result["predicted_price"],
        lower_bound=result["uncertainty"]["lower_bound"],
        upper_bound=result["uncertainty"]["upper_bound"],
        reliability=result["reliability"]["level"],
        recommendation=result["fair_listing"]["recommendation"],
        property_data=json.dumps(property_data),
    )
    db.session.add(prediction)
    return prediction


def what_if_properties(data) -> tuple[dict, dict, dict]:
    """Return the original, modified and displayed change dictionaries."""
    base = property_from_payload(data, area_default=1500, bhk_default=3)
    changes = {}
    if data.get("change_bhk"):
        changes["bhk"] = int(data["change_bhk"])
    if data.get("change_area"):
        changes["area_sqft"] = float(data["change_area"])
    if data.get("change_bathrooms"):
        changes["bathrooms"] = int(data["change_bathrooms"])
    if data.get("change_age"):
        changes["property_age"] = int(data["change_age"])

    modified = base.copy()
    modified.update(changes)
    return base, modified, changes


def api_what_if_properties(data) -> tuple[dict, dict]:
    """Preserve the additive ``change_area`` behavior of the established API."""
    base = property_from_payload(data, area_default=1500, bhk_default=3)
    modified = dict(base)
    if data.get("change_bhk") not in (None, ""):
        modified["bhk"] = int(data["change_bhk"])
    if data.get("change_bathrooms") not in (None, ""):
        modified["bathrooms"] = int(data["change_bathrooms"])
    if data.get("change_age") not in (None, ""):
        modified["property_age"] = int(data["change_age"])
    if data.get("change_area") not in (None, ""):
        modified["area_sqft"] = float(base["area_sqft"]) + float(
            data["change_area"]
        )
    return base, modified


def normalize_bulk_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Accept the historical CSV column aliases used by bulk valuation."""
    column_map = {}
    for column in dataframe.columns:
        normalized = column.lower().strip()
        if normalized in ("property_type", "type", "buildtype"):
            column_map[column] = "property_type"
        elif normalized in ("city", "location_city"):
            column_map[column] = "city"
        elif normalized in ("locality", "location", "area_name", "address"):
            column_map[column] = "locality"
        elif normalized in (
            "area",
            "area_sqft",
            "size",
            "total_area",
            "super area",
        ):
            column_map[column] = "area_sqft"
        elif normalized in ("bhk", "bedrooms", "no. of bedrooms", "bedroom"):
            column_map[column] = "bhk"
        elif normalized in ("bathrooms", "bath", "bathroom"):
            column_map[column] = "bathrooms"
    return dataframe.rename(columns=column_map)


def bulk_valuate(dataframe: pd.DataFrame) -> list[dict]:
    """Value bulk rows and retain the browser table's original response shape."""
    dataframe = normalize_bulk_columns(dataframe)
    engine = get_engine()
    results = []

    for index, row in dataframe.iterrows():
        property_data = {
            "property_type": str(row.get("property_type", "Apartment")),
            "city": str(row.get("city", "Hyderabad")),
            "locality": str(row.get("locality", "")),
            "area_sqft": float(row.get("area_sqft", 1000)),
            "bhk": int(row.get("bhk", 2))
            if pd.notna(row.get("bhk"))
            else 2,
            "bathrooms": int(row.get("bathrooms", 2))
            if pd.notna(row.get("bathrooms"))
            else 2,
            "property_age": int(row.get("property_age", 5))
            if pd.notna(row.get("property_age"))
            else 5,
        }
        prediction = engine.predict(property_data)
        if "error" in prediction:
            continue
        results.append(
            {
                "property_id": index + 1,
                "property_type": property_data["property_type"],
                "city": property_data["city"],
                "locality": property_data["locality"],
                "area_sqft": property_data["area_sqft"],
                "bhk": property_data["bhk"],
                "predicted_price": prediction["predicted_price"],
                "lower_bound": prediction["uncertainty"]["lower_bound"],
                "upper_bound": prediction["uncertainty"]["upper_bound"],
                "price_per_sqft": prediction["price_per_sqft"],
                "reliability": prediction["reliability"]["level"],
                "ood_flag": prediction["ood"]["is_ood"],
                "recommendation": prediction["fair_listing"]["recommendation"],
            }
        )

    return results
