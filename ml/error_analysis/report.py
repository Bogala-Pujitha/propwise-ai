from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def summarize_errors(
    residual_path: str | Path = "data/processed/hyderabad_residuals.csv",
    output_path: str | Path = "data/processed/error_analysis.json",
) -> dict:
    """Produce error summaries by property type and locality."""
    residual_path = Path(residual_path)
    output_path = Path(output_path)

    df = pd.read_csv(residual_path)

    report = {
        "rows": int(len(df)),
        "overall": {
            "mean_absolute_error": float(df["absolute_error"].mean()),
            "median_absolute_error": float(df["absolute_error"].median()),
            "mean_absolute_percentage_error": float(
                df["absolute_percentage_error"].mean()
            ),
            "under_prediction_rate_pct": float(
                (df["direction"] == "under_predicted").mean() * 100
            ),
            "over_prediction_rate_pct": float(
                (df["direction"] == "over_predicted").mean() * 100
            ),
        },
        "by_property_type": (
            df.groupby("property_type")
            .agg(
                rows=("price", "size"),
                mae=("absolute_error", "mean"),
                median_error=("absolute_error", "median"),
                mape=("absolute_percentage_error", "mean"),
            )
            .round(2)
            .reset_index()
            .to_dict(orient="records")
        ),
    }

    if "locality" in df.columns:
        report["worst_localities"] = (
            df.groupby("locality")
            .agg(
                rows=("price", "size"),
                mae=("absolute_error", "mean"),
                mape=("absolute_percentage_error", "mean"),
            )
            .query("rows >= 3")
            .sort_values("mae", ascending=False)
            .head(20)
            .round(2)
            .reset_index()
            .to_dict(orient="records")
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    print(json.dumps(summarize_errors(), indent=2))
