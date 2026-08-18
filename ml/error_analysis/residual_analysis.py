from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PROPERTY_TYPES = ("Apartment", "House", "Villa", "Plot")


def build_residual_table(
    test_path: str | Path = "data/processed/hyderabad_test.csv",
    models_dir: str | Path = "models",
    output_path: str | Path = "data/processed/hyderabad_residuals.csv",
) -> pd.DataFrame:
    """Create row-level prediction errors for the locked Hyderabad set."""
    test_path = Path(test_path)
    models_dir = Path(models_dir)
    output_path = Path(output_path)

    df = pd.read_csv(test_path)
    feature_engineer = joblib.load(models_dir / "feature_engineer.joblib")
    frames = []

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

        subset["predicted_price"] = predicted
        subset["residual"] = actual - predicted
        subset["absolute_error"] = np.abs(subset["residual"])
        subset["absolute_percentage_error"] = (
            subset["absolute_error"]
            / np.where(actual == 0, 1.0, actual)
            * 100.0
        )
        subset["direction"] = np.where(
            subset["residual"] >= 0,
            "under_predicted",
            "over_predicted",
        )
        frames.append(subset)

    if not frames:
        raise ValueError("No matching model/test data was found")

    result = pd.concat(frames, ignore_index=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


if __name__ == "__main__":
    result = build_residual_table()
    print(f"Residual rows written: {len(result)}")
