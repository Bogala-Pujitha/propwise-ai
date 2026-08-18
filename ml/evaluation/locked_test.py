from __future__ import annotations

from pathlib import Path
import hashlib

import pandas as pd


def create_locked_hyderabad_test(
    master_path="data/processed/master_dataset.csv",
    output_path="data/processed/hyderabad_test.csv",
    test_fraction=0.20,
):
    master_path = Path(master_path)
    output_path = Path(output_path)

    if not master_path.exists():
        raise FileNotFoundError(str(master_path))

    df = pd.read_csv(master_path)
    required = {"city", "property_type", "price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    hyd = df[
        df["city"].astype(str).str.strip().str.lower().eq("hyderabad")
    ].copy()

    if hyd.empty:
        raise ValueError("No Hyderabad rows found.")

    def stable(row):
        raw = "|".join(
            str(row.get(c, ""))
            for c in ["property_id", "city", "locality",
                      "property_type", "area_sqft", "price"]
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    hyd["_hash"] = hyd.apply(stable, axis=1)
    hyd = hyd.sort_values("_hash")

    target = max(1, round(len(hyd) * test_fraction))
    chosen = []

    for _, group in hyd.groupby("property_type", dropna=False):
        if len(chosen) >= target:
            break
        chosen.append(group.iloc[0])

    chosen_hashes = {row["_hash"] for row in chosen}
    for _, row in hyd.iterrows():
        if len(chosen) >= target:
            break
        if row["_hash"] not in chosen_hashes:
            chosen.append(row)
            chosen_hashes.add(row["_hash"])

    result = pd.DataFrame(chosen).drop(columns=["_hash"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    return result


if __name__ == "__main__":
    result = create_locked_hyderabad_test()
    print("Locked rows:", len(result))
