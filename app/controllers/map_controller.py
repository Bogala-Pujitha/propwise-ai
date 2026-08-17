from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.services.geocoding import (
    get_city_coords,
    get_locality_coords,
)

map_bp = Blueprint(
    "map_api",
    __name__,
    url_prefix="/api/map"
)


def _df():
    from app import MASTER_DF
    return MASTER_DF


def _normalise_type(value):
    value = str(value).strip().lower()

    aliases = {
        "apartment": "Apartment",
        "flat": "Apartment",
        "house": "House",
        "independent house": "House",
        "villa": "Villa",
        "plot": "Plot",
        "land": "Plot",
    }

    return aliases.get(
        value,
        str(value).title()
    )


def _number(row, names):
    for name in names:
        if name not in row:
            continue

        value = row[name]

        if value in (None, ""):
            continue

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if value == value:
            return value

    return None


@map_bp.get("/options")
@login_required
def options():
    df = _df()

    if df is None or len(df) == 0:
        return jsonify({
            "cities": [],
            "localities": {},
            "property_types": [
                "Apartment",
                "House",
                "Villa",
                "Plot"
            ]
        })

    cities = []

    if "city" in df.columns:
        cities = sorted({
            str(value).strip()
            for value in df["city"].dropna()
            if str(value).strip()
        })

    localities = {}

    if (
        "city" in df.columns
        and "locality" in df.columns
    ):
        for city in cities:
            rows = df.loc[
                df["city"]
                .astype(str)
                .str.strip()
                .str.casefold()
                == city.casefold(),
                "locality"
            ]

            localities[city] = sorted({
                str(value).strip()
                for value in rows.dropna()
                if str(value).strip()
            })

    property_types = []

    if "property_type" in df.columns:
        property_types = sorted({
            _normalise_type(value)
            for value in df["property_type"].dropna()
            if str(value).strip()
        })

    return jsonify({
        "cities": cities,
        "localities": localities,
        "property_types": property_types or [
            "Apartment",
            "House",
            "Villa",
            "Plot"
        ]
    })


@map_bp.get("/properties")
@login_required
def properties():
    df = _df()

    if df is None or len(df) == 0:
        return jsonify({
            "count": 0,
            "properties": []
        })

    city = (
        request.args.get("city") or ""
    ).strip()

    locality = (
        request.args.get("locality") or ""
    ).strip()

    property_type = (
        request.args.get("property_type") or ""
    ).strip()

    working = df.copy()

    if city and "city" in working.columns:
        working = working[
            working["city"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == city.casefold()
        ]

    if locality and "locality" in working.columns:
        working = working[
            working["locality"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == locality.casefold()
        ]

    if (
        property_type
        and "property_type" in working.columns
    ):
        normalized = working[
            "property_type"
        ].map(_normalise_type)

        working = working[
            normalized.str.casefold()
            == property_type.casefold()
        ]

    working = working.head(500)

    output = []

    for index, row in working.iterrows():
        row_city = str(
            row.get(
                "city",
                city or "Hyderabad"
            )
        ).strip()

        row_locality = str(
            row.get(
                "locality",
                ""
            )
        ).strip()

        ptype = _normalise_type(
            row.get(
                "property_type",
                "Apartment"
            )
        )

        lat = _number(
            row,
            ["latitude", "lat", "Latitude"]
        )

        lng = _number(
            row,
            [
                "longitude",
                "lon",
                "lng",
                "Longitude"
            ]
        )

        approximate = False

        if lat is None or lng is None:
            coords = (
                get_locality_coords(
                    row_city,
                    row_locality
                )
                if row_locality
                else get_city_coords(row_city)
            )

            lat = float(coords["lat"])
            lng = float(coords["lon"])
            approximate = True

        output.append({
            "id": str(
                row.get(
                    "property_id",
                    row.get("id", index)
                )
            ),
            "city": row_city,
            "locality": row_locality,
            "property_type": ptype,
            "area_sqft": _number(
                row,
                [
                    "area_sqft",
                    "area",
                    "Area",
                    "total_area"
                ]
            ),
            "bhk": row.get(
                "bhk",
                row.get("BHK")
            ),
            "price": _number(
                row,
                [
                    "price",
                    "Price",
                    "predicted_price"
                ]
            ),
            "latitude": lat,
            "longitude": lng,
            "approximate": approximate
        })

    return jsonify({
        "count": len(output),
        "properties": output
    })
