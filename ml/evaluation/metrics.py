from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)


def regression_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    positive = y_true > 0
    safe_true = np.where(y_true == 0, 1.0, y_true)
    pct_error = np.abs(y_true - y_pred) / safe_true

    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "R2": float(r2_score(y_true, y_pred)),
        "MAPE": float(
            mean_absolute_percentage_error(
                y_true[positive], y_pred[positive]
            ) * 100
        ) if positive.any() else 0.0,
        "within_10_pct": float((pct_error <= 0.10).mean() * 100),
        "within_20_pct": float((pct_error <= 0.20).mean() * 100),
        "n": int(len(y_true)),
    }
