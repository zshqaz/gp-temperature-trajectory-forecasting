from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SmoothMeanModel:
    hour_smoothing: float = 10.0
    year_knots: int = 4
    year_smoothing: float = 0.01
    coefficients_: np.ndarray | None = None
    year_min_: float | None = None
    year_span_: float | None = None
    knots_: np.ndarray | None = None

    def fit(self, curves: np.ndarray, years: np.ndarray) -> "SmoothMeanModel":
        if curves.ndim != 2 or curves.shape[1] != 24:
            raise ValueError("curves must have shape (n_days, 24)")
        self.year_min_ = float(np.min(years))
        self.year_span_ = max(float(np.max(years) - self.year_min_), 1.0)
        if self.year_knots > 0:
            self.knots_ = np.linspace(0.0, 1.0, self.year_knots + 2)[1:-1]
        else:
            self.knots_ = np.empty(0, dtype=float)

        n_days = curves.shape[0]
        hours = np.tile(np.arange(24), n_days)
        repeated_years = np.repeat(years.astype(float), 24)
        x = self._design(hours, repeated_years)
        y = curves.reshape(-1)
        penalty = self._penalty(x.shape[1])
        system = x.T @ x + penalty + np.eye(x.shape[1]) * 1e-10
        self.coefficients_ = np.linalg.solve(system, x.T @ y)
        return self

    def predict_curves(self, years: np.ndarray) -> np.ndarray:
        self._check_fitted()
        years = np.asarray(years, dtype=float)
        hours = np.tile(np.arange(24), len(years))
        repeated_years = np.repeat(years, 24)
        prediction = self._design(hours, repeated_years) @ self.coefficients_
        return prediction.reshape(len(years), 24)

    def _year_basis(self, years: np.ndarray) -> np.ndarray:
        z = (np.asarray(years, dtype=float) - self.year_min_) / self.year_span_
        columns = [z, z**2, z**3]
        for knot in self.knots_:
            columns.append(np.maximum(z - knot, 0.0) ** 3)
        return np.column_stack(columns)

    def _design(self, hours: np.ndarray, years: np.ndarray) -> np.ndarray:
        hour_basis = np.eye(24, dtype=float)[np.asarray(hours, dtype=int)]
        return np.column_stack([hour_basis, self._year_basis(years)])

    def _penalty(self, n_coefficients: int) -> np.ndarray:
        penalty = np.zeros((n_coefficients, n_coefficients), dtype=float)
        second_difference = np.zeros((24, 24), dtype=float)
        for i in range(24):
            second_difference[i, i] = -2.0
            second_difference[i, (i - 1) % 24] = 1.0
            second_difference[i, (i + 1) % 24] = 1.0
        penalty[:24, :24] = (
            self.hour_smoothing * second_difference.T @ second_difference
        )
        year_dimension = n_coefficients - 24
        year_penalty = np.ones(year_dimension, dtype=float) * self.year_smoothing
        if year_dimension:
            year_penalty[0] = 0.0
        penalty[24:, 24:] = np.diag(year_penalty)
        return penalty

    def _check_fitted(self) -> None:
        if self.coefficients_ is None:
            raise RuntimeError("SmoothMeanModel is not fitted.")

