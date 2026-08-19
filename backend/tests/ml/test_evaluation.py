import numpy as np

from ml.evaluation.metrics import regression_metrics


def test_metrics():
    result = regression_metrics(
        np.array([100.0, 200.0, 300.0]),
        np.array([110.0, 190.0, 300.0]),
    )
    assert result["n"] == 3
    assert result["within_20_pct"] == 100.0
