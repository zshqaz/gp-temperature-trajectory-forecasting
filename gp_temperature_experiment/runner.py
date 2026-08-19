from __future__ import annotations

import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .data import load_july_curves
from .mean import SmoothMeanModel
from .models import (
    fit_analog,
    fit_functional_ridge,
    fit_persistence,
    make_gp_conditioner,
)
from .optimize import fit_kernel
from .scores import evaluate_forecast, paired_comparisons


class ExperimentRunner:
    def __init__(self, config: dict):
        self.config = config
        self.output_root = Path(config["output_root"]).resolve()
        self.logs_dir = self.output_root / "logs"
        self.metrics_dir = self.output_root / "metrics"
        self.diagnostics_dir = self.output_root / "diagnostics"
        self.provenance_dir = self.output_root / "provenance"
        self.predictions_dir = self.output_root / "predictions"
        for directory in (
            self.output_root,
            self.logs_dir,
            self.metrics_dir,
            self.diagnostics_dir,
            self.provenance_dir,
            self.predictions_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        self.progress_path = self.logs_dir / "progress.jsonl"
        self.start_time = time.monotonic()
        self.daily_rows: list[dict[str, object]] = []
        self.horizon_rows: list[dict[str, object]] = []
        self.optimization_rows: list[dict[str, object]] = []
        self._last_heartbeat = 0.0

    def run(self) -> Path:
        self._event("run_started", command=" ".join(sys.argv))
        self._write_environment()
        effective_config = {
            key: value for key, value in self.config.items() if not key.startswith("_")
        }
        self._write_json(
            self.provenance_dir / "frozen_config.yaml", effective_config
        )

        curve_data = load_july_curves(self.config)
        curves_frame = curve_data.curves
        self._write_json(self.provenance_dir / "data_audit.json", curve_data.audit)
        self._event("data_gate_passed", **curve_data.audit)

        analysis = self.config["analysis"]
        observed_hours = analysis["observed_hours"]
        future_hours = analysis["future_hours"]
        all_curves = curves_frame[list(range(24))].to_numpy(dtype=float)
        all_years = curves_frame["year"].to_numpy(dtype=int)
        all_dates = curves_frame.index.to_numpy(dtype=str)

        for test_year in range(
            analysis["test_year_start"], analysis["test_year_end"] + 1
        ):
            self._check_timeout()
            train_mask = all_years < test_year
            test_mask = all_years == test_year
            if not np.any(test_mask):
                raise RuntimeError(f"No held-out July days found for {test_year}.")
            train_curves = all_curves[train_mask]
            train_years = all_years[train_mask]
            test_curves = all_curves[test_mask]
            test_years = all_years[test_mask]
            test_dates = all_dates[test_mask]
            self._event(
                "fold_started",
                test_year=test_year,
                training_days=int(len(train_curves)),
                test_days=int(len(test_curves)),
            )

            mean_config = self.config["mean_model"]
            mean_model = SmoothMeanModel(
                hour_smoothing=mean_config["hour_smoothing"],
                year_knots=mean_config["year_knots"],
                year_smoothing=mean_config["year_smoothing"],
            ).fit(train_curves, train_years)
            train_mean = mean_model.predict_curves(train_years)
            test_mean = mean_model.predict_curves(test_years)
            train_residuals = train_curves - train_mean
            test_residuals = test_curves - test_mean

            gp_conditioners = {}
            optimization = self.config["optimization"]
            for kernel_index, kernel in enumerate(self.config["kernels"]):
                self._check_timeout()
                result = fit_kernel(
                    kernel=kernel,
                    residuals=train_residuals,
                    starts=optimization["starts"],
                    max_evaluations_per_start=optimization[
                        "max_evaluations_per_start"
                    ],
                    relative_tolerance=optimization["relative_tolerance"],
                    seed=optimization["seed"] + test_year * 100 + kernel_index,
                )
                for row in result.diagnostics:
                    row["test_year"] = test_year
                    row["best_for_fold"] = bool(
                        np.isclose(row["objective"], result.objective)
                    )
                    self.optimization_rows.append(row)
                gp_conditioners[f"gp_{kernel}"] = make_gp_conditioner(
                    kernel, result.params, observed_hours, future_hours
                )
                self._event(
                    "kernel_fitted",
                    test_year=test_year,
                    kernel=kernel,
                    objective=result.objective,
                    converged=result.converged,
                    evaluations=result.evaluations,
                )
                self._checkpoint_optimization()

            baseline_config = self.config["baselines"]
            persistence = fit_persistence(
                train_curves,
                future_hours,
                baseline_config["covariance_ridge"],
            )
            analog = fit_analog(
                train_residuals,
                observed_hours,
                future_hours,
                baseline_config["analog_k"],
            )
            functional = fit_functional_ridge(
                train_residuals,
                observed_hours,
                future_hours,
                baseline_config["functional_ridge"],
                baseline_config["covariance_ridge"],
            )
            thresholds = self._atypical_thresholds(
                train_curves, train_residuals, observed_hours, future_hours
            )

            model_names = [*gp_conditioners, "baseline_persistence", "baseline_analog", "baseline_functional"]
            draws = self.config["posterior"]["draws"]
            base_seed = self.config["posterior"]["seed"]
            for day_index, (date, actual, residual, mean_curve) in enumerate(
                zip(test_dates, test_curves, test_residuals, test_mean)
            ):
                flags = self._atypical_flags(
                    actual,
                    residual,
                    observed_hours,
                    future_hours,
                    thresholds,
                )
                for model_index, model_name in enumerate(model_names):
                    rng = np.random.default_rng(
                        base_seed
                        + test_year * 100_000
                        + day_index * 100
                        + model_index
                    )
                    if model_name.startswith("gp_"):
                        _, samples = gp_conditioners[model_name].forecast(
                            residual[observed_hours],
                            mean_curve[future_hours],
                            draws,
                            rng,
                        )
                    elif model_name == "baseline_persistence":
                        _, samples = persistence.forecast(actual[9], draws, rng)
                    elif model_name == "baseline_analog":
                        _, samples = analog.forecast(
                            residual[observed_hours],
                            mean_curve[future_hours],
                            draws,
                            rng,
                        )
                    else:
                        _, samples = functional.forecast(
                            residual[observed_hours],
                            mean_curve[future_hours],
                            draws,
                            rng,
                        )
                    daily, horizon = evaluate_forecast(
                        actual[future_hours], samples, future_hours
                    )
                    self.daily_rows.append(
                        {
                            "model": model_name,
                            "year": test_year,
                            "date": date,
                            **flags,
                            **daily,
                        }
                    )
                    for row in horizon:
                        self.horizon_rows.append(
                            {
                                "model": model_name,
                                "year": test_year,
                                "date": date,
                                **flags,
                                **row,
                            }
                        )
                self._heartbeat(
                    test_year=test_year,
                    completed_days=day_index + 1,
                    total_days=len(test_curves),
                )

            self._checkpoint_metrics()
            self._event(
                "fold_completed",
                test_year=test_year,
                accumulated_daily_rows=len(self.daily_rows),
            )

        self._finalize_metrics()
        result_path = self._write_result(status="completed")
        self._event(
            "run_completed",
            duration_seconds=round(time.monotonic() - self.start_time, 3),
            result_path=str(result_path),
        )
        return result_path

    def _atypical_thresholds(
        self,
        train_curves: np.ndarray,
        train_residuals: np.ndarray,
        observed_hours: list[int],
        future_hours: list[int],
    ) -> dict[str, object]:
        future = train_curves[:, future_hours]
        upper = float(np.quantile(future.max(axis=1), 0.95))
        rapid_values = np.max(np.abs(future[:, 3:] - future[:, :-3]), axis=1)
        rapid = float(np.quantile(rapid_values, 0.95))
        morning = train_residuals[:, observed_hours]
        center = morning.mean(axis=0)
        covariance_matrix = np.cov(morning, rowvar=False, ddof=1)
        covariance_matrix += np.eye(len(observed_hours)) * max(
            float(np.mean(np.diag(covariance_matrix))) * 1e-6, 1e-8
        )
        precision = np.linalg.inv(covariance_matrix)
        centered = morning - center
        distances = np.sqrt(np.einsum("ni,ij,nj->n", centered, precision, centered))
        unusual = float(np.quantile(distances, 0.95))
        return {
            "upper": upper,
            "rapid": rapid,
            "morning_center": center,
            "morning_precision": precision,
            "unusual": unusual,
        }

    def _atypical_flags(
        self,
        curve: np.ndarray,
        residual: np.ndarray,
        observed_hours: list[int],
        future_hours: list[int],
        thresholds: dict[str, object],
    ) -> dict[str, bool]:
        future = curve[future_hours]
        centered = residual[observed_hours] - thresholds["morning_center"]
        distance = float(
            np.sqrt(centered @ thresholds["morning_precision"] @ centered)
        )
        return {
            "upper_tail": bool(future.max() > thresholds["upper"]),
            "rapid_change": bool(
                np.max(np.abs(future[3:] - future[:-3])) > thresholds["rapid"]
            ),
            "unusual_morning": bool(distance > thresholds["unusual"]),
        }

    def _checkpoint_optimization(self) -> None:
        if self.optimization_rows:
            pd.DataFrame(self.optimization_rows).to_csv(
                self.diagnostics_dir / "optimization_starts.csv", index=False
            )

    def _checkpoint_metrics(self) -> None:
        pd.DataFrame(self.daily_rows).to_csv(
            self.metrics_dir / "day_level_scores.csv", index=False
        )
        pd.DataFrame(self.horizon_rows).to_csv(
            self.metrics_dir / "horizon_level_scores.csv", index=False
        )

    def _finalize_metrics(self) -> None:
        daily = pd.DataFrame(self.daily_rows)
        horizon = pd.DataFrame(self.horizon_rows)
        coverage_columns = [
            "nlpd",
            "crps",
            "pit",
            "standardized_residual",
            "cover_50",
            "width_50",
            "cover_80",
            "width_80",
            "cover_95",
            "width_95",
        ]
        (
            horizon.groupby(["model", "hour"], sort=True)[coverage_columns]
            .mean()
            .reset_index()
            .to_csv(self.metrics_dir / "coverage_by_horizon.csv", index=False)
        )
        comparisons = paired_comparisons(
            daily,
            reference_model=self.config["bootstrap"]["reference_model"],
            repetitions=self.config["bootstrap"]["repetitions"],
            seed=self.config["bootstrap"]["seed"],
        )
        comparisons.to_csv(self.metrics_dir / "paired_comparisons.csv", index=False)

        atypical_rows = []
        summary_metrics = [
            "nlpd",
            "crps",
            "energy",
            "variogram",
            "max_crps",
            "sim_cover_80",
            "sim_cover_95",
            "max_cover_80",
            "max_cover_95",
        ]
        for flag in ("upper_tail", "rapid_change", "unusual_morning"):
            subset = daily.loc[daily[flag]]
            if subset.empty:
                continue
            grouped = subset.groupby("model", sort=True)[summary_metrics].mean()
            counts = subset.groupby("model", sort=True).size().rename("n_days")
            frame = grouped.join(counts).reset_index()
            frame.insert(1, "stratum", flag)
            atypical_rows.append(frame)
        if atypical_rows:
            pd.concat(atypical_rows, ignore_index=True).to_csv(
                self.metrics_dir / "atypical_day_diagnostics.csv", index=False
            )

        model_summary = daily.groupby("model", sort=True)[
            [
                "nlpd",
                "crps",
                "energy",
                "variogram",
                "max_crps",
                "max_absolute_error",
                "max_bias",
                "sim_cover_80",
                "sim_cover_95",
                "max_cover_80",
                "max_cover_95",
            ]
        ].mean()
        model_summary.reset_index().to_csv(
            self.metrics_dir / "model_summary.csv", index=False
        )

    def _write_result(self, status: str) -> Path:
        duration = time.monotonic() - self.start_time
        now = datetime.now().astimezone().isoformat()
        result_path = self.output_root / "experiment_result_gp_temperature_v1.md"
        output_files = []
        for path in sorted(self.output_root.rglob("*")):
            if path.is_file() and path != result_path:
                output_files.append(
                    f"| `{path.relative_to(self.output_root)}` | {path.stat().st_size} |"
                )
        text = f"""## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: run
- Origin Date: {now}
- Verification Status: UNVERIFIED
- Version Label: exp_result_v1

## Experiment Result

- **ID**: {self.config['experiment_id']}
- **Type**: analysis and simulation
- **Status**: {status}
- **Command**: `{' '.join(sys.argv)}`
- **Working Directory**: `{Path.cwd()}`
- **Duration**: {duration:.3f} seconds
- **Exit Code**: 0

### Output Files

| File | Size (bytes) |
|---|---:|
{os.linesep.join(output_files)}

### Output Summary

- Test years: {self.config['analysis']['test_year_start']}–{self.config['analysis']['test_year_end']}
- Models: {len(self.config['kernels']) + 3}
- Day-level forecast records: {len(self.daily_rows)}
- Horizon-level forecast records: {len(self.horizon_rows)}
- Posterior draws per forecast: {self.config['posterior']['draws']}

### Anomalies Detected

See `diagnostics/optimization_starts.csv` and `logs/progress.jsonl`. Statistical interpretation has not yet been performed.
"""
        result_path.write_text(text, encoding="utf-8")
        return result_path

    def _write_environment(self) -> None:
        text = "\n".join(
            [
                f"python={sys.version}",
                f"executable={sys.executable}",
                f"platform={platform.platform()}",
                f"processor={platform.processor()}",
                f"numpy={np.__version__}",
                f"pandas={pd.__version__}",
                f"cpu_count={os.cpu_count()}",
            ]
        )
        (self.provenance_dir / "environment.txt").write_text(text + "\n", encoding="utf-8")

    def _event(self, event: str, **payload) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "elapsed_seconds": round(time.monotonic() - self.start_time, 3),
            **payload,
        }
        with self.progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=_json_default) + "\n")
        print(json.dumps(record, default=_json_default), flush=True)

    def _heartbeat(self, **payload) -> None:
        now = time.monotonic()
        interval = self.config["monitoring"]["heartbeat_seconds"]
        if now - self._last_heartbeat >= interval:
            self._last_heartbeat = now
            self._event("heartbeat", **payload)

    def _check_timeout(self) -> None:
        timeout = self.config["monitoring"]["hard_timeout_hours"] * 3600.0
        if time.monotonic() - self.start_time > timeout:
            raise TimeoutError(f"Hard timeout reached after {timeout} seconds.")

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, indent=2, default=_json_default) + "\n",
            encoding="utf-8",
        )


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    raise TypeError(f"Not JSON serializable: {type(value)!r}")


def run_experiment(config: dict) -> Path:
    return ExperimentRunner(config).run()
