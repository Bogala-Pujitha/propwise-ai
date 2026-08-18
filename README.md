# PropWise AI — Missing ML Files

This package contains only the ML files that are not currently represented as
dedicated packages in the public `main` branch:

- ml/evaluation/
- ml/error_analysis/

The current `ml/training/model_trainer.py` already contains Experiment A/B/C
and model selection logic, so no duplicate experiments package is included.

Placement:
propwise-ai/ml/evaluation/
propwise-ai/ml/error_analysis/
tests/ml/test_evaluation.py

Important:
The locked Hyderabad test generator creates a reproducible holdout artifact.
Because the current training code already trains with Hyderabad data, a newly
created holdout becomes a valid final test only after the final models are
retrained without that holdout.
