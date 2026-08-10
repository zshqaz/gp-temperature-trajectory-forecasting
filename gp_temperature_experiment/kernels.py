from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class KernelSpec:
    name: str
    parameter_names: tuple[str, ...]


SPECS = {
    "se": KernelSpec("se", ("log_variance", "log_length", "log_nugget")),
    "matern32": KernelSpec("matern32", ("log_variance", "log_length", "log_nugget")),
    "matern52": KernelSpec("matern52", ("log_variance", "log_length", "log_nugget")),
    "periodic": KernelSpec(
        "periodic", ("log_variance", "log_periodic_length", "log_nugget")
    ),
    "locally_periodic": KernelSpec(
        "locally_periodic",
        ("log_variance", "log_periodic_length", "log_local_length", "log_nugget"),
    ),
    "additive": KernelSpec(
        "additive",
        (
            "log_periodic_variance",
            "log_periodic_length",
            "log_matern_variance",
            "log_matern_length",
            "log_nugget",
        ),
    ),
}


def parameter_bounds(name: str, residual_variance: float) -> np.ndarray:
    variance = max(float(residual_variance), 1e-4)
    variance_bounds = (np.log(variance * 1e-3), np.log(variance * 1e2))
    nugget_bounds = (np.log(variance * 1e-6), np.log(variance * 2.0))
    length_bounds = (np.log(0.25), np.log(48.0))
    periodic_length_bounds = (np.log(0.1), np.log(10.0))
    if name in {"se", "matern32", "matern52"}:
        bounds = [variance_bounds, length_bounds, nugget_bounds]
    elif name == "periodic":
        bounds = [variance_bounds, periodic_length_bounds, nugget_bounds]
    elif name == "locally_periodic":
        bounds = [
            variance_bounds,
            periodic_length_bounds,
            length_bounds,
            nugget_bounds,
        ]
    elif name == "additive":
        bounds = [
            variance_bounds,
            periodic_length_bounds,
            variance_bounds,
            length_bounds,
            nugget_bounds,
        ]
    else:
        raise KeyError(f"Unknown kernel: {name}")
    return np.asarray(bounds, dtype=float)


def covariance(
    name: str,
    params: np.ndarray,
    x: np.ndarray | None = None,
    y: np.ndarray | None = None,
    include_nugget: bool = False,
) -> np.ndarray:
    if name not in SPECS:
        raise KeyError(f"Unknown kernel: {name}")
    x = np.arange(24, dtype=float) if x is None else np.asarray(x, dtype=float)
    y = x if y is None else np.asarray(y, dtype=float)
    distance = np.abs(x[:, None] - y[None, :])

    if name == "se":
        variance, length, nugget = np.exp(params)
        matrix = variance * np.exp(-0.5 * (distance / length) ** 2)
    elif name == "matern32":
        variance, length, nugget = np.exp(params)
        scaled = np.sqrt(3.0) * distance / length
        matrix = variance * (1.0 + scaled) * np.exp(-scaled)
    elif name == "matern52":
        variance, length, nugget = np.exp(params)
        scaled = np.sqrt(5.0) * distance / length
        matrix = variance * (1.0 + scaled + scaled**2 / 3.0) * np.exp(-scaled)
    elif name == "periodic":
        variance, periodic_length, nugget = np.exp(params)
        sine = np.sin(np.pi * distance / 24.0)
        matrix = variance * np.exp(-2.0 * sine**2 / periodic_length**2)
    elif name == "locally_periodic":
        variance, periodic_length, local_length, nugget = np.exp(params)
        sine = np.sin(np.pi * distance / 24.0)
        periodic = np.exp(-2.0 * sine**2 / periodic_length**2)
        scaled = np.sqrt(3.0) * distance / local_length
        local = (1.0 + scaled) * np.exp(-scaled)
        matrix = variance * periodic * local
    else:
        (
            periodic_variance,
            periodic_length,
            matern_variance,
            matern_length,
            nugget,
        ) = np.exp(params)
        sine = np.sin(np.pi * distance / 24.0)
        periodic = periodic_variance * np.exp(
            -2.0 * sine**2 / periodic_length**2
        )
        scaled = np.sqrt(3.0) * distance / matern_length
        matern = matern_variance * (1.0 + scaled) * np.exp(-scaled)
        matrix = periodic + matern

    if include_nugget:
        if x.shape == y.shape and np.array_equal(x, y):
            matrix = matrix + np.eye(len(x)) * nugget
        else:
            raise ValueError("Nugget can only be added to a square self-covariance.")
    return matrix

