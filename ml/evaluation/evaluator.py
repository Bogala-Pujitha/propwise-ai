from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .metrics import regression_metrics


PROPERTY_TYPES = ("Apartment", "House", "Villa", "Plot")


def evaluate_models(
    test_path="data/processed/hyderabad_test.csv",
    models_dir="models",
    output_path="data/processed/hyderabad_evaluation.json",
):
    test_path = Path(test_path)
    models_dir = Path(models_dir)
    output_path = Path(output_path)

    df = pd.read_csv(test_path)
    feature_engineer = joblib.load(models_dir / "feature_engineer.joblib")

    results = {"test_path": str(test_path), "property_types": {}}

    for property_type in PROPERTY_TYPES:
        model_path = models_dir / f"{property_type.lower()}_model.joblib"
        if not model_path.exists():
            continue

        subset = df[
            df["property_type"].astype(str).str.strip().str.lower()
            == property_type.lower()
        ].copy()

        if subset.empty:
            continue

        model = joblib.load(model_path)
        X = feature_engineer.transform(subset, fit=False)
        actual = subset["price"].astype(float).to_numpy()
        predicted = np.expm1(model.predict(X))

        results["property_types"][property_type] = regression_metrics(
            actual, predicted
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
