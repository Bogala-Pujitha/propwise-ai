import json
import os

EXPERIMENTS = {
    "experiment_a": "Experiment A: Hyderabad Only",
    "experiment_b": "Experiment B: India-Wide",
    "experiment_c": "Experiment C: Hybrid",
}


def _read(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return None


def discover_experiments(models_dir):
    result = {
        key: {
            "label": label,
            "models": {}
        }
        for key, label in EXPERIMENTS.items()
    }

    for root, _dirs, files in os.walk(models_dir):
        for filename in files:
            if not filename.endswith(
                "_metadata.json"
            ):
                continue

            metadata = _read(
                os.path.join(
                    root,
                    filename
                )
            )

            if not isinstance(metadata, dict):
                continue

            experiment = str(
                metadata.get("experiment")
                or metadata.get("experiment_name")
                or ""
            ).strip().lower()

            if not experiment:
                relative = (
                    os.path.relpath(
                        root,
                        models_dir
                    )
                    .replace(chr(92), "/")
                    .lower()
                )

                for key in EXPERIMENTS:
                    if key in relative:
                        experiment = key
                        break

            if experiment not in result:
                continue

            property_type = (
                metadata.get("property_type")
                or filename.replace(
                    "_metadata.json",
                    ""
                )
            )

            result[experiment]["models"][
                str(property_type)
            ] = metadata

    best = _read(
        os.path.join(
            models_dir,
            "all_models_metadata.json"
        )
    )

    if isinstance(best, dict):
        for property_type, metadata in best.items():
            if not isinstance(metadata, dict):
                continue

            experiment = str(
                metadata.get("best_experiment")
                or metadata.get("experiment")
                or metadata.get("experiment_name")
                or ""
            ).strip().lower()

            if (
                experiment in result
                and property_type not in
                result[experiment]["models"]
            ):
                result[experiment]["models"][
                    property_type
                ] = metadata

    return result
