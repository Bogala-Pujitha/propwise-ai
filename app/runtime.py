"""Lazy runtime resources used by valuation and map features."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from flask import current_app


@dataclass
class PropWiseRuntime:
    """Own the lazily loaded ML engine and its supporting dataset."""

    project_root: Path
    valuation_engine: object | None = None
    master_df: object | None = None
    dropdown_data: dict | None = None

    @property
    def models_dir(self) -> Path:
        return self.project_root / "models"

    @property
    def master_dataset_path(self) -> Path:
        return self.project_root / "data" / "processed" / "master_dataset.csv"

    def initialize(self):
        """Load resources on demand, preserving the original startup behavior."""
        if self.valuation_engine is not None and self.dropdown_data is not None:
            return self

        from app.services.geocoding import get_all_dropdown_data
        from app.services.valuation_engine import ValuationEngine

        if self.master_dataset_path.exists():
            self.master_df = pd.read_csv(self.master_dataset_path)

        try:
            self.valuation_engine = ValuationEngine(
                str(self.models_dir),
                self.master_df,
            )
        except Exception:
            self.valuation_engine = None

        try:
            self.dropdown_data = get_all_dropdown_data(self.master_df)
        except Exception:
            self.dropdown_data = {}

        return self


def get_runtime(app=None) -> PropWiseRuntime:
    """Return the runtime container registered on the active Flask app."""
    if app is None:
        app = current_app
    return app.extensions["propwise_runtime"]
