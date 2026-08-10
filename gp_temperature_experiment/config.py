from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    """Load the JSON-compatible YAML configuration used by this project."""
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config["_config_path"] = str(config_path)
    _validate(config)
    return config


def _validate(config: dict[str, Any]) -> None:
    required = {
        "experiment_id",
        "version_label",
        "data_path",
        "expected_sha256",
        "output_root",
        "analysis",
        "mean_model",
        "kernels",
        "optimization",
        "posterior",
        "baselines",
        "bootstrap",
        "monitoring",
    }
    missing = sorted(required.difference(config))
    if missing:
        raise ValueError(f"Missing configuration keys: {missing}")

    analysis = config["analysis"]
    observed = analysis["observed_hours"]
    future = analysis["future_hours"]
    if observed != list(range(0, 10)):
        raise ValueError("Primary observed_hours must be local hours 0 through 9.")
    if future != list(range(10, 24)):
        raise ValueError("Primary future_hours must be local hours 10 through 23.")
    if analysis.get("local_duplicate_hour_policy") != "mean":
        raise ValueError("local_duplicate_hour_policy must be explicitly set to 'mean'.")
    if analysis["test_year_start"] > analysis["test_year_end"]:
        raise ValueError("test_year_start must not exceed test_year_end.")
    if config["optimization"]["starts"] < 1:
        raise ValueError("At least one optimization start is required.")
    if config["posterior"]["draws"] < 20:
        raise ValueError("At least 20 posterior draws are required.")
