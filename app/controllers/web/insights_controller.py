"""Browser controller for market, map, model and experiment views."""

from flask import render_template
from flask_login import login_required

from app.runtime import get_runtime
from app.services.dashboard_service import (
    experiments_context,
    market_intelligence as build_market_intelligence,
    model_metadata,
)


@login_required
def market_intelligence():
    runtime = get_runtime()
    if runtime.master_df is None:
        runtime.initialize()
    return render_template(
        "market_intelligence.html",
        city_stats=build_market_intelligence(runtime.master_df),
    )


@login_required
def map_view():
    return render_template("map.html")


@login_required
def model_performance():
    runtime = get_runtime()
    return render_template(
        "model_performance.html",
        metadata=model_metadata(runtime.models_dir),
    )


@login_required
def experiments():
    runtime = get_runtime()
    experiment_data, best_models = experiments_context(runtime.models_dir)
    return render_template(
        "experiments.html",
        experiments=experiment_data,
        best_models=best_models,
    )
