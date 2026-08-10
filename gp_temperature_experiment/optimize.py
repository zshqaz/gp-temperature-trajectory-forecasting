from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .kernels import covariance, parameter_bounds


@dataclass
class OptimizationResult:
    kernel: str
    params: np.ndarray
    objective: float
    converged: bool
    evaluations: int
    diagnostics: list[dict[str, object]]


def replicated_gp_nll(kernel: str, params: np.ndarray, scatter: np.ndarray, n_days: int) -> float:
    try:
        matrix = covariance(kernel, params, include_nugget=True)
        jitter = max(float(np.mean(np.diag(matrix))) * 1e-10, 1e-12)
        factor = np.linalg.cholesky(matrix + np.eye(24) * jitter)
        logdet = 2.0 * np.log(np.diag(factor)).sum()
        inverse_scatter = np.linalg.solve(factor.T, np.linalg.solve(factor, scatter))
        quadratic = float(np.trace(inverse_scatter))
        value = 0.5 * (n_days * logdet + quadratic + n_days * 24 * np.log(2.0 * np.pi))
        if not np.isfinite(value):
            return float("inf")
        return value
    except (np.linalg.LinAlgError, FloatingPointError, ValueError):
        return float("inf")


def fit_kernel(
    kernel: str,
    residuals: np.ndarray,
    starts: int,
    max_evaluations_per_start: int,
    relative_tolerance: float,
    seed: int,
) -> OptimizationResult:
    residual_variance = float(np.var(residuals))
    bounds = parameter_bounds(kernel, residual_variance)
    scatter = residuals.T @ residuals
    rng = np.random.default_rng(seed)
    initial_points = [np.mean(bounds, axis=1)]
    initial_points.extend(
        rng.uniform(bounds[:, 0], bounds[:, 1]) for _ in range(starts - 1)
    )

    diagnostics: list[dict[str, object]] = []
    best_params: np.ndarray | None = None
    best_objective = float("inf")
    total_evaluations = 0

    for start_index, initial in enumerate(initial_points):
        params, objective, evaluations, converged = _pattern_search(
            lambda value: replicated_gp_nll(kernel, value, scatter, residuals.shape[0]),
            initial,
            bounds,
            max_evaluations_per_start,
            relative_tolerance,
        )
        total_evaluations += evaluations
        diagnostics.append(
            {
                "kernel": kernel,
                "start": start_index,
                "objective": objective,
                "converged": bool(converged),
                "evaluations": evaluations,
                "boundary_hit": bool(
                    np.any(np.isclose(params, bounds[:, 0], atol=1e-3))
                    or np.any(np.isclose(params, bounds[:, 1], atol=1e-3))
                ),
                **{f"param_{i}": float(value) for i, value in enumerate(params)},
            }
        )
        if objective < best_objective:
            best_objective = objective
            best_params = params.copy()

    if best_params is None or not np.isfinite(best_objective):
        raise RuntimeError(f"No finite optimization result for kernel {kernel}")
    return OptimizationResult(
        kernel=kernel,
        params=best_params,
        objective=float(best_objective),
        converged=any(bool(row["converged"]) for row in diagnostics),
        evaluations=total_evaluations,
        diagnostics=diagnostics,
    )


def _pattern_search(
    objective,
    initial: np.ndarray,
    bounds: np.ndarray,
    max_evaluations: int,
    relative_tolerance: float,
) -> tuple[np.ndarray, float, int, bool]:
    current = np.clip(np.asarray(initial, dtype=float), bounds[:, 0], bounds[:, 1])
    current_value = float(objective(current))
    evaluations = 1
    step = np.maximum((bounds[:, 1] - bounds[:, 0]) * 0.2, 0.05)
    converged = False

    while evaluations < max_evaluations:
        previous_value = current_value
        improved = False
        for dimension in range(len(current)):
            for direction in (-1.0, 1.0):
                candidate = current.copy()
                candidate[dimension] = np.clip(
                    candidate[dimension] + direction * step[dimension],
                    bounds[dimension, 0],
                    bounds[dimension, 1],
                )
                if candidate[dimension] == current[dimension]:
                    continue
                candidate_value = float(objective(candidate))
                evaluations += 1
                if candidate_value < current_value:
                    current = candidate
                    current_value = candidate_value
                    improved = True
                if evaluations >= max_evaluations:
                    break
            if evaluations >= max_evaluations:
                break
        if not improved:
            step *= 0.5
        relative_change = abs(previous_value - current_value) / max(
            abs(previous_value), 1.0
        )
        if np.max(step) < 1e-3 or (
            not improved and relative_change < relative_tolerance and np.max(step) < 0.02
        ):
            converged = True
            break
    return current, current_value, evaluations, converged

