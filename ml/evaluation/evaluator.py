from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .metrics import regression_metrics


PROPERTY_TYPES = ("Apartment", "House", "Villa", "Plot")


def evaluate_models(
    test_path: str | Path = "data/processed/hyderabad_test.csv",
    models_dir: str | Path = "models",
    output_path: str | Path = "data/processed/hyderabad_evaluation.json",
) -> dict:
    """Evaluate current deployed property-type models on a locked test set."""
    test_path = Path(test_path)
    models_dir = Path(models_dir)
    output_path = Path(output_path)

    if not test_path.exists():
        raise FileNotFoundError(
            f"Locked test set not found: {test_path}"
        )

    df = pd.read_csv(test_path)

    for col in ("price", "property_type"):
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    fe_path = models_dir / "feature_engineer.joblib"
    if not fe_path.exists():
        raise FileNotFoundError(f"Feature engineer not found: {fe_path}")

    feature_engineer = joblib.load(fe_path)
    results = {
        "test_path": str(test_path),
        "models_dir": str(models_dir),
        "property_types": {},
    }

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

        y_true = subset["price"].astype(float).to_numpy()
        y_pred = np.expm1(model.predict(X))

        results["property_types"][property_type] = regression_metrics(
            y_true, y_pred
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )
    return results


if __name__ == "__main__":
    print(json.dumps(evaluate_models(), indent=2))
