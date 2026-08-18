from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


DEFAULT_MASTER = Path("data/processed/master_dataset.csv")
DEFAULT_OUTPUT = Path("data/processed/hyderabad_test.csv")


def _stable_hash(row: pd.Series) -> str:
    raw = "|".join(
        str(row.get(col, ""))
        for col in (
            "property_id",
            "city",
            "locality",
            "property_type",
            "area_sqft",
            "price",
        )
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_locked_hyderabad_test(
    master_path: str | Path = DEFAULT_MASTER,
    output_path: str | Path = DEFAULT_OUTPUT,
    test_fraction: float = 0.20,
) -> pd.DataFrame:
    """Create a deterministic Hyderabad holdout artifact."""
    if not 0.05 <= test_fraction <= 0.50:
        raise ValueError("test_fraction must be between 0.05 and 0.50")

    master_path = Path(master_path)
    output_path = Path(output_path)

    if not master_path.exists():
        raise FileNotFoundError(f"Master dataset not found: {master_path}")

    df = pd.read_csv(master_path)
    required = {"city", "property_type", "price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    hyd = df[
        df["city"].astype(str).str.strip().str.lower().eq("hyderabad")
    ].copy()

    if hyd.empty:
        raise ValueError("No Hyderabad rows found")

    hyd["_stable_hash"] = hyd.apply(_stable_hash, axis=1)
    hyd = hyd.sort_values("_stable_hash").reset_index(drop=True)

    target_count = max(1, int(round(len(hyd) * test_fraction)))

    # Try to represent each available property type.
    first_by_type = (
        hyd.groupby("property_type", dropna=False, sort=False)
        .head(1)
        .copy()
    )

    selected_ids = set()
    selected = []
    for idx, row in first_by_type.iterrows():
        if len(selected) < target_count:
            selected.append(row)
            selected_ids.add(idx)

    remaining = hyd.drop(index=list(selected_ids), errors="ignore")
    needed = max(0, target_count - len(selected))
    if needed:
        selected.extend(remaining.head(needed).to_dict("records"))

    test_df = pd.DataFrame(selected).drop(columns=["_stable_hash"], errors="ignore")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    test_df.to_csv(output_path, index=False)
    return test_df


if __name__ == "__main__":
    result = create_locked_hyderabad_test()
    print(f"Locked Hyderabad rows: {len(result)}")
    print(f"Saved: {DEFAULT_OUTPUT}")
