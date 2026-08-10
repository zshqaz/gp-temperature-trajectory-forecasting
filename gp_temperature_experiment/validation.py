from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


PRIMARY_METRICS = ("nlpd", "crps", "energy", "variogram", "max_crps")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def benjamini_hochberg(p_values: np.ndarray) -> np.ndarray:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    ranked = values[order]
    adjusted_ranked = ranked * len(values) / np.arange(1, len(values) + 1)
    adjusted_ranked = np.minimum.accumulate(adjusted_ranked[::-1])[::-1]
    adjusted = np.empty_like(adjusted_ranked)
    adjusted[order] = np.minimum(adjusted_ranked, 1.0)
    return adjusted


def paired_signflip_tests(
    daily: pd.DataFrame,
    reference: str,
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ref = daily.loc[daily["model"] == reference].set_index("date")
    rows: list[dict[str, object]] = []
    for model in sorted(daily["model"].unique()):
        if model == reference:
            continue
        candidate = daily.loc[daily["model"] == model].set_index("date")
        shared = candidate.index.intersection(ref.index)
        for metric in PRIMARY_METRICS:
            difference = candidate.loc[shared, metric] - ref.loc[shared, metric]
            years = candidate.loc[shared, "year"].astype(int)
            year_means = (
                pd.DataFrame({"year": years, "difference": difference})
                .groupby("year", sort=True)["difference"]
                .mean()
                .to_numpy()
            )
            observed = float(difference.mean())
            signs = rng.choice(
                np.array([-1.0, 1.0]), size=(repetitions, len(year_means)), replace=True
            )
            null_means = (signs * year_means[None, :]).mean(axis=1)
            p_value = (1.0 + np.sum(np.abs(null_means) >= abs(observed))) / (
                repetitions + 1.0
            )
            reference_mean = float(ref.loc[shared, metric].mean())
            rows.append(
                {
                    "model": model,
                    "reference": reference,
                    "metric": metric,
                    "mean_difference": observed,
                    "relative_difference": observed / max(abs(reference_mean), 1e-12),
                    "signflip_p": float(p_value),
                    "test_years": int(len(year_means)),
                }
            )
    result = pd.DataFrame(rows)
    result["bh_fdr_p"] = benjamini_hochberg(result["signflip_p"].to_numpy())
    result["bh_fdr_reject_0_05"] = result["bh_fdr_p"] <= 0.05
    return result


def coverage_intervals(
    daily: pd.DataFrame,
    horizon: pd.DataFrame,
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    sources = [
        (horizon, "marginal_cover_50", "cover_50", 0.50),
        (horizon, "marginal_cover_80", "cover_80", 0.80),
        (horizon, "marginal_cover_95", "cover_95", 0.95),
        (daily, "simultaneous_cover_80", "sim_cover_80", 0.80),
        (daily, "simultaneous_cover_95", "sim_cover_95", 0.95),
        (daily, "maximum_cover_80", "max_cover_80", 0.80),
        (daily, "maximum_cover_95", "max_cover_95", 0.95),
    ]
    rows: list[dict[str, object]] = []
    for frame, label, column, nominal in sources:
        for model, group in frame.groupby("model", sort=True):
            year_means = group.groupby("year", sort=True)[column].mean().to_numpy()
            sampled = rng.choice(
                year_means, size=(repetitions, len(year_means)), replace=True
            ).mean(axis=1)
            estimate = float(group[column].mean())
            rows.append(
                {
                    "model": model,
                    "coverage_type": label,
                    "nominal": nominal,
                    "estimate": estimate,
                    "deviation": estimate - nominal,
                    "ci_lower": float(np.quantile(sampled, 0.025)),
                    "ci_upper": float(np.quantile(sampled, 0.975)),
                    "test_years": int(len(year_means)),
                }
            )
    return pd.DataFrame(rows)


def reproducibility_comparison(original: Path, rerun: Path) -> pd.DataFrame:
    relative_files = sorted(
        path.relative_to(original)
        for path in original.rglob("*")
        if path.is_file() and path.name != "experiment_result_gp_temperature_v1.md"
    )
    rows = []
    for relative in relative_files:
        original_path = original / relative
        rerun_path = rerun / relative
        exists = rerun_path.exists()
        original_hash = sha256(original_path)
        rerun_hash = sha256(rerun_path) if exists else ""
        rows.append(
            {
                "file": str(relative),
                "original_bytes": original_path.stat().st_size,
                "rerun_bytes": rerun_path.stat().st_size if exists else -1,
                "original_sha256": original_hash,
                "rerun_sha256": rerun_hash,
                "exact_match": bool(exists and original_hash == rerun_hash),
            }
        )
    return pd.DataFrame(rows)


def run_validation(
    original: Path,
    rerun: Path,
    output: Path,
    repetitions: int = 10_000,
    seed: int = 314159,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    daily = pd.read_csv(original / "metrics" / "day_level_scores.csv")
    horizon = pd.read_csv(original / "metrics" / "horizon_level_scores.csv")
    paired = paired_signflip_tests(
        daily, reference="gp_matern32", repetitions=repetitions, seed=seed
    )
    coverage = coverage_intervals(
        daily, horizon, repetitions=repetitions, seed=seed + 1
    )
    reproducibility = reproducibility_comparison(original, rerun)
    paired.to_csv(output / "paired_signflip_fdr.csv", index=False)
    coverage.to_csv(output / "coverage_year_block_intervals.csv", index=False)
    reproducibility.to_csv(output / "reproducibility_comparison.csv", index=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate experiment outputs.")
    parser.add_argument("--original", required=True)
    parser.add_argument("--rerun", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repetitions", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=314159)
    args = parser.parse_args(argv)
    run_validation(
        Path(args.original).resolve(),
        Path(args.rerun).resolve(),
        Path(args.output).resolve(),
        repetitions=args.repetitions,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

