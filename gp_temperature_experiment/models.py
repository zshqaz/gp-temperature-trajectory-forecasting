from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .kernels import covariance


def regularize_covariance(matrix: np.ndarray, ridge: float = 1e-6) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    matrix = (matrix + matrix.T) * 0.5
    scale = max(float(np.mean(np.diag(matrix))), 1.0)
    return matrix + np.eye(matrix.shape[0]) * ridge * scale


def gaussian_samples(
    mean: np.ndarray, covariance_matrix: np.ndarray, draws: int, rng: np.random.Generator
) -> np.ndarray:
    covariance_matrix = regularize_covariance(covariance_matrix)
    try:
        factor = np.linalg.cholesky(covariance_matrix)
    except np.linalg.LinAlgError:
        values, vectors = np.linalg.eigh(covariance_matrix)
        values = np.maximum(values, 1e-10)
        factor = vectors @ np.diag(np.sqrt(values))
    return mean[None, :] + rng.standard_normal((draws, len(mean))) @ factor.T


@dataclass(frozen=True)
class GPConditioner:
    gain: np.ndarray
    covariance: np.ndarray

    def forecast(
        self,
        observed_residual: np.ndarray,
        future_mean: np.ndarray,
        draws: int,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        mean = future_mean + self.gain @ observed_residual
        return mean, gaussian_samples(mean, self.covariance, draws, rng)


def make_gp_conditioner(
    kernel: str,
    params: np.ndarray,
    observed_hours: list[int],
    future_hours: list[int],
) -> GPConditioner:
    observed = np.asarray(observed_hours, dtype=float)
    future = np.asarray(future_hours, dtype=float)
    k_oo = covariance(kernel, params, observed, observed, include_nugget=True)
    k_ff = covariance(kernel, params, future, future, include_nugget=True)
    k_fo = covariance(kernel, params, future, observed, include_nugget=False)
    k_oo = regularize_covariance(k_oo, ridge=1e-10)
    gain = np.linalg.solve(k_oo, k_fo.T).T
    conditional_covariance = k_ff - gain @ k_fo.T
    conditional_covariance = regularize_covariance(conditional_covariance)
    return GPConditioner(gain=gain, covariance=conditional_covariance)


@dataclass(frozen=True)
class PersistenceBaseline:
    offsets: np.ndarray
    covariance: np.ndarray

    def forecast(
        self, observed_nine: float, draws: int, rng: np.random.Generator
    ) -> tuple[np.ndarray, np.ndarray]:
        mean = observed_nine + self.offsets
        return mean, gaussian_samples(mean, self.covariance, draws, rng)


def fit_persistence(
    train_curves: np.ndarray, future_hours: list[int], ridge: float
) -> PersistenceBaseline:
    errors = train_curves[:, future_hours] - train_curves[:, [9]]
    offsets = errors.mean(axis=0)
    covariance_matrix = np.cov(errors, rowvar=False, ddof=1)
    return PersistenceBaseline(offsets, regularize_covariance(covariance_matrix, ridge))


@dataclass(frozen=True)
class FunctionalRidgeBaseline:
    coefficients: np.ndarray
    covariance: np.ndarray

    def forecast(
        self,
        observed_residual: np.ndarray,
        future_mean: np.ndarray,
        draws: int,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        mean = future_mean + observed_residual @ self.coefficients
        return mean, gaussian_samples(mean, self.covariance, draws, rng)


def fit_functional_ridge(
    train_residuals: np.ndarray,
    observed_hours: list[int],
    future_hours: list[int],
    ridge_lambda: float,
    covariance_ridge: float,
) -> FunctionalRidgeBaseline:
    x = train_residuals[:, observed_hours]
    y = train_residuals[:, future_hours]
    scale = max(float(np.trace(x.T @ x) / len(observed_hours)), 1.0)
    coefficients = np.linalg.solve(
        x.T @ x + np.eye(len(observed_hours)) * ridge_lambda * scale / len(x),
        x.T @ y,
    )
    errors = y - x @ coefficients
    covariance_matrix = regularize_covariance(
        np.cov(errors, rowvar=False, ddof=1), covariance_ridge
    )
    return FunctionalRidgeBaseline(coefficients, covariance_matrix)


@dataclass(frozen=True)
class AnalogBaseline:
    train_observed_z: np.ndarray
    train_future_residuals: np.ndarray
    observed_center: np.ndarray
    observed_scale: np.ndarray
    k: int

    def forecast(
        self,
        observed_residual: np.ndarray,
        future_mean: np.ndarray,
        draws: int,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        standardized = (observed_residual - self.observed_center) / self.observed_scale
        distances = np.sqrt(np.mean((self.train_observed_z - standardized) ** 2, axis=1))
        k = min(self.k, len(distances))
        nearest = np.argpartition(distances, k - 1)[:k]
        local_distances = distances[nearest]
        bandwidth = max(float(np.median(local_distances)), 1e-6)
        weights = np.exp(-0.5 * (local_distances / bandwidth) ** 2)
        weights = weights / weights.sum()
        future_ensemble = future_mean[None, :] + self.train_future_residuals[nearest]
        mean = np.average(future_ensemble, axis=0, weights=weights)
        selected = rng.choice(k, size=draws, replace=True, p=weights)
        samples = future_ensemble[selected]
        return mean, samples


def fit_analog(
    train_residuals: np.ndarray,
    observed_hours: list[int],
    future_hours: list[int],
    k: int,
) -> AnalogBaseline:
    observed = train_residuals[:, observed_hours]
    center = observed.mean(axis=0)
    scale = observed.std(axis=0, ddof=1)
    scale = np.where(scale < 1e-8, 1.0, scale)
    return AnalogBaseline(
        train_observed_z=(observed - center) / scale,
        train_future_residuals=train_residuals[:, future_hours],
        observed_center=center,
        observed_scale=scale,
        k=k,
    )

