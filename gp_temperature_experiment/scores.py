from __future__ import annotations

import numpy as np
import pandas as pd


def normal_cdf(values: np.ndarray) -> np.ndarray:
    """Vectorized standard normal CDF with absolute error below about 1e-7."""
    values = np.asarray(values, dtype=float)
    absolute = np.abs(values)
    t = 1.0 / (1.0 + 0.2316419 * absolute)
    polynomial = (
        0.319381530 * t
        - 0.356563782 * t**2
        + 1.781477937 * t**3
        - 1.821255978 * t**4
        + 1.330274429 * t**5
    )
    density = np.exp(-0.5 * absolute**2) / np.sqrt(2.0 * np.pi)
    positive = 1.0 - density * polynomial
    return np.where(values >= 0.0, positive, 1.0 - positive)


def ensemble_crps(samples: np.ndarray, observation: np.ndarray) -> np.ndarray:
    samples = np.asarray(samples, dtype=float)
    observation = np.asarray(observation, dtype=float)
    n = samples.shape[0]
    first = np.mean(np.abs(samples - observation[None, :]), axis=0)
    ordered = np.sort(samples, axis=0)
    coefficients = 2.0 * np.arange(1, n + 1) - n - 1.0
    pair_half = np.sum(coefficients[:, None] * ordered, axis=0) / (n * n)
    return first - pair_half


def sample_crps(samples: np.ndarray, observation: float) -> float:
    values = np.sort(np.asarray(samples, dtype=float))
    n = len(values)
    first = float(np.mean(np.abs(values - observation)))
    coefficients = 2.0 * np.arange(1, n + 1) - n - 1.0
    return first - float(np.sum(coefficients * values) / (n * n))


def evaluate_forecast(
    observation: np.ndarray,
    samples: np.ndarray,
    future_hours: list[int],
) -> tuple[dict[str, float], list[dict[str, float]]]:
    observation = np.asarray(observation, dtype=float)
    samples = np.asarray(samples, dtype=float)
    forecast_mean = samples.mean(axis=0)
    forecast_sd = np.maximum(samples.std(axis=0, ddof=1), 1e-6)
    z = (observation - forecast_mean) / forecast_sd
    nlpd = (
        0.5 * np.log(2.0 * np.pi)
        + np.log(forecast_sd)
        + 0.5 * z**2
    )
    crps = ensemble_crps(samples, observation)
    pit = (
        np.sum(samples < observation[None, :], axis=0)
        + 0.5 * np.sum(samples == observation[None, :], axis=0)
        + 0.5
    ) / (samples.shape[0] + 1.0)

    central_levels = (0.50, 0.80, 0.95)
    interval_values: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for level in central_levels:
        alpha = (1.0 - level) * 0.5
        lower, upper = np.quantile(samples, [alpha, 1.0 - alpha], axis=0)
        interval_values[level] = (lower, upper)

    pair_a = samples[0::2]
    pair_b = samples[1::2]
    pair_count = min(len(pair_a), len(pair_b))
    energy = float(
        np.mean(np.linalg.norm(samples - observation[None, :], axis=1))
        - 0.5
        * np.mean(np.linalg.norm(pair_a[:pair_count] - pair_b[:pair_count], axis=1))
    )

    variogram = _variogram_score(observation, samples, future_hours, order=0.5)
    standardized_draws = (samples - forecast_mean[None, :]) / forecast_sd[None, :]
    max_standardized = np.max(np.abs(standardized_draws), axis=1)

    maximum_samples = samples.max(axis=1)
    observed_maximum = float(observation.max())
    median_maximum = float(np.median(maximum_samples))

    daily: dict[str, float] = {
        "nlpd": float(np.mean(nlpd)),
        "crps": float(np.mean(crps)),
        "energy": energy,
        "variogram": variogram,
        "max_crps": sample_crps(maximum_samples, observed_maximum),
        "max_absolute_error": abs(median_maximum - observed_maximum),
        "max_bias": median_maximum - observed_maximum,
        "observed_maximum": observed_maximum,
        "forecast_maximum_median": median_maximum,
    }

    for level in central_levels:
        lower, upper = interval_values[level]
        label = int(level * 100)
        simultaneous_quantile = float(np.quantile(max_standardized, level))
        simultaneous_lower = forecast_mean - simultaneous_quantile * forecast_sd
        simultaneous_upper = forecast_mean + simultaneous_quantile * forecast_sd
        maximum_lower, maximum_upper = np.quantile(
            maximum_samples, [(1.0 - level) * 0.5, 1.0 - (1.0 - level) * 0.5]
        )
        daily[f"sim_cover_{label}"] = float(
            np.all(
                (observation >= simultaneous_lower)
                & (observation <= simultaneous_upper)
            )
        )
        daily[f"sim_width_{label}"] = float(
            np.mean(simultaneous_upper - simultaneous_lower)
        )
        daily[f"max_cover_{label}"] = float(
            maximum_lower <= observed_maximum <= maximum_upper
        )
        daily[f"max_width_{label}"] = float(maximum_upper - maximum_lower)

    horizon_rows: list[dict[str, float]] = []
    for position, hour in enumerate(future_hours):
        row: dict[str, float] = {
            "hour": float(hour),
            "observation": float(observation[position]),
            "forecast_mean": float(forecast_mean[position]),
            "forecast_sd": float(forecast_sd[position]),
            "nlpd": float(nlpd[position]),
            "crps": float(crps[position]),
            "pit": float(pit[position]),
            "standardized_residual": float(z[position]),
        }
        for level in central_levels:
            lower, upper = interval_values[level]
            label = int(level * 100)
            row[f"cover_{label}"] = float(
                lower[position] <= observation[position] <= upper[position]
            )
            row[f"width_{label}"] = float(upper[position] - lower[position])
        horizon_rows.append(row)
    return daily, horizon_rows


def _variogram_score(
    observation: np.ndarray,
    samples: np.ndarray,
    future_hours: list[int],
    order: float,
) -> float:
    hours = np.asarray(future_hours, dtype=float)
    total = 0.0
    weights = []
    terms = []
    for i in range(len(hours)):
        for j in range(i + 1, len(hours)):
            weight = 1.0 / abs(hours[j] - hours[i])
            observed_term = abs(observation[i] - observation[j]) ** order
            forecast_term = float(
                np.mean(np.abs(samples[:, i] - samples[:, j]) ** order)
            )
            weights.append(weight)
            terms.append((observed_term - forecast_term) ** 2)
    weights_array = np.asarray(weights, dtype=float)
    weights_array /= weights_array.sum()
    for weight, term in zip(weights_array, terms):
        total += float(weight * term)
    return total


def paired_comparisons(
    daily: pd.DataFrame,
    reference_model: str,
    repetitions: int,
    seed: int,
) -> pd.DataFrame:
    metrics = ["nlpd", "crps", "energy", "variogram", "max_crps"]
    rng = np.random.default_rng(seed)
    reference = daily.loc[daily["model"] == reference_model, ["date", "year", *metrics]]
    reference = reference.set_index("date")
    rows: list[dict[str, object]] = []
    for model in sorted(daily["model"].unique()):
        if model == reference_model:
            continue
        candidate = daily.loc[daily["model"] == model, ["date", "year", *metrics]]
        candidate = candidate.set_index("date")
        shared = candidate.index.intersection(reference.index)
        if len(shared) == 0:
            continue
        years = candidate.loc[shared, "year"].astype(int)
        for metric in metrics:
            differences = candidate.loc[shared, metric] - reference.loc[shared, metric]
            frame = pd.DataFrame({"year": years, "difference": differences})
            year_means = frame.groupby("year", sort=True)["difference"].mean().to_numpy()
            if len(year_means) == 0:
                continue
            sampled = rng.choice(
                year_means, size=(repetitions, len(year_means)), replace=True
            ).mean(axis=1)
            rows.append(
                {
                    "model": model,
                    "reference": reference_model,
                    "metric": metric,
                    "mean_difference": float(differences.mean()),
                    "median_difference": float(differences.median()),
                    "ci_lower": float(np.quantile(sampled, 0.025)),
                    "ci_upper": float(np.quantile(sampled, 0.975)),
                    "fraction_years_favoring": float(np.mean(year_means < 0.0)),
                    "test_years": int(len(year_means)),
                }
            )
    return pd.DataFrame(rows)

