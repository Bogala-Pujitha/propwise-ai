from flask import Blueprint, jsonify, request
from flask_login import login_required

from backend.runtime import get_runtime
from backend.services.geocoding import (
    get_city_coords,
    get_locality_coords,
)

map_bp = Blueprint(
    "map_api",
    __name__,
    url_prefix="/api/map",
)


def _df():
    runtime = get_runtime()

    if runtime.master_df is None:
        runtime.initialize()

    return runtime.master_df


def _engine():
    runtime = get_runtime().initialize()

    if runtime.valuation_engine is None:
        raise RuntimeError("Valuation engine is unavailable")

    return runtime.valuation_engine


def _normalise_type(value):
    value = str(value).strip().lower()

    aliases = {
        "apartment": "Apartment",
        "flat": "Apartment",
        "house": "House",
        "independent house": "House",
        "independenthouse": "House",
        "villa": "Villa",
        "plot": "Plot",
        "land": "Plot",
    }

    return aliases.get(
        value,
        str(value).title(),
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


def _coordinates_for_row(row, city="", locality=""):
    """
    Get property coordinates.

    Priority:
    1. Real property latitude/longitude from dataset
    2. Locality coordinates
    3. City coordinates
    """

    row_city = str(
        row.get("city", city or "Hyderabad")
    ).strip()

    row_locality = str(
        row.get("locality", locality or "")
    ).strip()

    lat = _number(
        row,
        ["latitude", "lat", "Latitude"],
    )

    lng = _number(
        row,
        [
            "longitude",
            "lon",
            "lng",
            "Longitude",
        ],
    )

    approximate = False

    if lat is None or lng is None:

        if row_locality:
            coords = get_locality_coords(
                row_city,
                row_locality,
            )
        else:
            coords = get_city_coords(
                row_city,
            )

        lat = float(coords["lat"])
        lng = float(coords["lon"])

        approximate = True

    return (
        row_city,
        row_locality,
        lat,
        lng,
        approximate,
    )


def _property_payload(row, index, city="", locality=""):
    (
        row_city,
        row_locality,
        lat,
        lng,
        approximate,
    ) = _coordinates_for_row(
        row,
        city=city,
        locality=locality,
    )

    property_type = _normalise_type(
        row.get(
            "property_type",
            "Apartment",
        )
    )

    property_id = row.get(
        "property_id",
        row.get("id", index),
    )

    return {
        "id": str(property_id),
        "city": row_city,
        "locality": row_locality,
        "property_type": property_type,

        "area_sqft": _number(
            row,
            [
                "area_sqft",
                "area",
                "Area",
                "total_area",
            ],
        ),

        "bhk": row.get(
            "bhk",
            row.get("BHK"),
        ),

        "bathrooms": row.get(
            "bathrooms",
            row.get("Bath"),
        ),

        "price": _number(
            row,
            [
                "price",
                "Price",
                "predicted_price",
            ],
        ),

        "latitude": lat,
        "longitude": lng,

        "approximate": approximate,
    }


@map_bp.get("/options")
@login_required
def options():
    df = _df()

    if df is None or len(df) == 0:
        return jsonify(
            {
                "cities": [],
                "localities": {},
                "property_types": [
                    "Apartment",
                    "House",
                    "Villa",
                    "Plot",
                ],
            }
        )

    cities = []

    if "city" in df.columns:
        cities = sorted(
            {
                str(value).strip()
                for value in df["city"].dropna()
                if str(value).strip()
            }
        )

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
                "locality",
            ]

            localities[city] = sorted(
                {
                    str(value).strip()
                    for value in rows.dropna()
                    if str(value).strip()
                }
            )

    property_types = []

    if "property_type" in df.columns:
        property_types = sorted(
            {
                _normalise_type(value)
                for value in df["property_type"].dropna()
                if str(value).strip()
            }
        )

    return jsonify(
        {
            "cities": cities,
            "localities": localities,
            "property_types": (
                property_types
                or [
                    "Apartment",
                    "House",
                    "Villa",
                    "Plot",
                ]
            ),
        }
    )


@map_bp.get("/properties")
@login_required
def properties():
    """
    Map 3 data source.

    Returns properties from the selected city/locality.
    Property type is optional so that Map 3 can display
    all four property types together.
    """

    df = _df()

    if df is None or len(df) == 0:
        return jsonify(
            {
                "count": 0,
                "properties": [],
            }
        )

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

    # Keep Map 3 responsive.
    working = working.head(500)

    output = []

    for index, row in working.iterrows():

        try:
            payload = _property_payload(
                row,
                index,
                city=city,
                locality=locality,
            )

            output.append(payload)

        except Exception:
            continue

    return jsonify(
        {
            "count": len(output),
            "properties": output,
        }
    )

@map_bp.post("/selected-property")
@login_required
def selected_property():
    """
    Find the dataset property that best matches the
    property currently selected in the valuation form.

    Priority:
    1. Same city
    2. Same locality
    3. Same property type
    4. Closest area
    5. Closest BHK

    Coordinates always come from dataset latitude/longitude
    when available. Existing coordinate fallback remains active.
    """

    data = (
        request.get_json(silent=True)
        or {}
    )

    city = str(
        data.get("city", "")
        or ""
    ).strip()

    locality = str(
        data.get("locality", "")
        or ""
    ).strip()

    property_type = _normalise_type(
        data.get(
            "property_type",
            "Apartment",
        )
    )

    try:
        area_sqft = float(
            data.get(
                "area_sqft",
                0,
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        area_sqft = 0

    try:
        bhk = float(
            data.get(
                "bhk",
                0,
            )
            or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        bhk = 0

    df = _df()

    if (
        df is None
        or len(df) == 0
    ):
        return jsonify(
            {
                "property": None
            }
        )

    working = df.copy()

    # ---------------------------------------------------------
    # CITY
    # ---------------------------------------------------------

    if (
        city
        and "city" in working.columns
    ):

        working = working[
            working["city"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == city.casefold()
        ]


    # ---------------------------------------------------------
    # LOCALITY
    # ---------------------------------------------------------

    if (
        locality
        and "locality" in working.columns
    ):

        locality_filtered = working[
            working["locality"]
            .astype(str)
            .str.strip()
            .str.casefold()
            == locality.casefold()
        ]

        if len(locality_filtered) > 0:
            working = locality_filtered


    if len(working) == 0:

        return jsonify(
            {
                "property": None
            }
        )


    # ---------------------------------------------------------
    # PROPERTY TYPE
    # ---------------------------------------------------------

    if "property_type" in working.columns:

        normalized_types = (
            working["property_type"]
            .map(_normalise_type)
        )

        type_filtered = working[
            normalized_types.str.casefold()
            == property_type.casefold()
        ]

        if len(type_filtered) > 0:
            working = type_filtered


    # ---------------------------------------------------------
    # BUILD DISTANCE SCORE
    # ---------------------------------------------------------

    scored = []

    for index, row in working.iterrows():

        row_area = _number(
            row,
            [
                "area_sqft",
                "area",
                "Area",
                "total_area",
            ],
        )

        row_bhk = _number(
            row,
            [
                "bhk",
                "BHK",
                "bedrooms",
            ],
        )

        area_difference = (
            abs(row_area - area_sqft)
            if row_area is not None
            and area_sqft > 0
            else 999999999
        )

        bhk_difference = (
            abs(row_bhk - bhk)
            if row_bhk is not None
            and bhk > 0
            else 999999999
        )

        # Area gets more weight than BHK.
        score = (
            area_difference
            +
            (bhk_difference * 500)
        )

        scored.append(
            (
                score,
                index,
                row,
            )
        )


    if not scored:

        return jsonify(
            {
                "property": None
            }
        )


    scored.sort(
        key=lambda item: item[0]
    )

    _, best_index, best_row = (
        scored[0]
    )


    try:

        property_payload = (
            _property_payload(
                best_row,
                best_index,
                city=city,
                locality=locality,
            )
        )

    except Exception:

        return jsonify(
            {
                "property": None
            }
        )


    return jsonify(
        {
            "property": property_payload
        }
    )


@map_bp.post("/comparables")
@login_required
def comparable_map_data():
    """
    Map 2 data source.

    Takes the same property data used for valuation,
    asks the comparable engine for comparable properties,
    then attaches coordinates to each comparable.
    """

    data = (
        request.get_json(silent=True)
        or {}
    )

    property_data = {
        "property_type": data.get(
            "property_type",
            "Apartment",
        ),
        "city": data.get(
            "city",
            "Hyderabad",
        ),
        "locality": data.get(
            "locality",
            "",
        ),
        "area_sqft": float(
            data.get(
                "area_sqft",
                0,
            )
            or 0
        ),
        "bhk": int(
            data.get(
                "bhk",
                2,
            )
            or 2
        ),
        "bathrooms": int(
            data.get(
                "bathrooms",
                2,
            )
            or 2
        ),
        "property_age": int(
            data.get(
                "property_age",
                5,
            )
            or 5
        ),
    }

    comparables = []

    try:
        engine = _engine()

        comparables = (
            engine
            .comparable_engine
            .find_comparables(
                property_data
            )
            or []
        )

    except Exception:
        comparables = []

    results = []

    for index, comparable in enumerate(
        comparables
    ):

        if not isinstance(
            comparable,
            dict,
        ):
            continue

        city = str(
            comparable.get(
                "city",
                property_data["city"],
            )
        ).strip()

        locality = str(
            comparable.get(
                "locality",
                property_data["locality"],
            )
        ).strip()

        property_type = _normalise_type(
            comparable.get(
                "property_type",
                property_data["property_type"],
            )
        )

        lat = _number(
            comparable,
            [
                "latitude",
                "lat",
                "Latitude",
            ],
        )

        lng = _number(
            comparable,
            [
                "longitude",
                "lon",
                "lng",
                "Longitude",
            ],
        )

        approximate = False

        if lat is None or lng is None:

            try:

                if locality:
                    coords = get_locality_coords(
                        city,
                        locality,
                    )
                else:
                    coords = get_city_coords(
                        city,
                    )

                lat = float(
                    coords["lat"]
                )

                lng = float(
                    coords["lon"]
                )

                approximate = True

            except Exception:
                continue

        results.append(
            {
                "id": str(
                    comparable.get(
                        "property_id",
                        comparable.get(
                            "id",
                            index,
                        ),
                    )
                ),

                "city": city,

                "locality": locality,

                "property_type":
                    property_type,

                "area_sqft":
                    _number(
                        comparable,
                        [
                            "area_sqft",
                            "area",
                            "Area",
                        ],
                    ),

                "bhk":
                    comparable.get(
                        "bhk",
                        comparable.get(
                            "bedrooms"
                        ),
                    ),

                "bathrooms":
                    comparable.get(
                        "bathrooms"
                    ),

                "price":
                    _number(
                        comparable,
                        [
                            "price",
                            "Price",
                            "predicted_price",
                        ],
                    ),

                "latitude":
                    lat,

                "longitude":
                    lng,

                "approximate":
                    approximate,
            }
        )

    return jsonify(
        {
            "count": len(results),
            "properties": results,
        }
    )