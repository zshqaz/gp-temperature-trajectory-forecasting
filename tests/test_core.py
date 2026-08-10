from __future__ import annotations

import unittest

import numpy as np

from gp_temperature_experiment.kernels import SPECS, covariance
from gp_temperature_experiment.mean import SmoothMeanModel
from gp_temperature_experiment.models import make_gp_conditioner
from gp_temperature_experiment.optimize import fit_kernel
from gp_temperature_experiment.scores import ensemble_crps, evaluate_forecast, normal_cdf


class KernelTests(unittest.TestCase):
    def test_all_kernel_covariances_are_positive_definite(self) -> None:
        parameters = {
            "se": np.log([4.0, 3.0, 0.1]),
            "matern32": np.log([4.0, 3.0, 0.1]),
            "matern52": np.log([4.0, 3.0, 0.1]),
            "periodic": np.log([4.0, 1.0, 0.1]),
            "locally_periodic": np.log([4.0, 1.0, 6.0, 0.1]),
            "additive": np.log([2.0, 1.0, 2.0, 6.0, 0.1]),
        }
        self.assertEqual(set(parameters), set(SPECS))
        for name, params in parameters.items():
            with self.subTest(kernel=name):
                matrix = covariance(name, params, include_nugget=True)
                self.assertTrue(np.allclose(matrix, matrix.T))
                self.assertGreater(np.linalg.eigvalsh(matrix).min(), 0.0)

    def test_gp_conditioner_dimensions(self) -> None:
        conditioner = make_gp_conditioner(
            "matern32", np.log([4.0, 3.0, 0.1]), list(range(10)), list(range(10, 24))
        )
        self.assertEqual(conditioner.gain.shape, (14, 10))
        self.assertEqual(conditioner.covariance.shape, (14, 14))
        self.assertGreater(np.linalg.eigvalsh(conditioner.covariance).min(), 0.0)


class MeanModelTests(unittest.TestCase):
    def test_mean_model_recovers_shapes(self) -> None:
        years = np.repeat(np.arange(2000, 2005), 3)
        hours = np.arange(24)
        base = 15.0 + 4.0 * np.sin(2.0 * np.pi * hours / 24.0)
        curves = np.vstack([base + 0.1 * (year - 2000) for year in years])
        model = SmoothMeanModel().fit(curves, years)
        predicted = model.predict_curves(np.array([2005, 2006]))
        self.assertEqual(predicted.shape, (2, 24))
        self.assertTrue(np.isfinite(predicted).all())


class OptimizerTests(unittest.TestCase):
    def test_optimizer_returns_finite_fit(self) -> None:
        rng = np.random.default_rng(7)
        true_covariance = covariance(
            "matern32", np.log([3.0, 4.0, 0.2]), include_nugget=True
        )
        residuals = rng.multivariate_normal(np.zeros(24), true_covariance, size=40)
        result = fit_kernel(
            "matern32",
            residuals,
            starts=2,
            max_evaluations_per_start=40,
            relative_tolerance=1e-4,
            seed=11,
        )
        self.assertTrue(np.isfinite(result.objective))
        self.assertEqual(result.params.shape, (3,))
        self.assertEqual(len(result.diagnostics), 2)


class ScoreTests(unittest.TestCase):
    def test_normal_cdf_reference_points(self) -> None:
        values = normal_cdf(np.array([-1.96, 0.0, 1.96]))
        np.testing.assert_allclose(values, [0.025, 0.5, 0.975], atol=1e-4)

    def test_ensemble_crps_is_nonnegative(self) -> None:
        rng = np.random.default_rng(3)
        samples = rng.normal(size=(1000, 2))
        score = ensemble_crps(samples, np.array([0.0, 1.0]))
        self.assertTrue(np.all(score >= 0.0))

    def test_forecast_metrics_have_expected_dimensions(self) -> None:
        rng = np.random.default_rng(5)
        observation = np.linspace(10.0, 20.0, 14)
        samples = observation + rng.normal(scale=1.0, size=(200, 14))
        daily, horizon = evaluate_forecast(observation, samples, list(range(10, 24)))
        self.assertEqual(len(horizon), 14)
        self.assertIn("energy", daily)
        self.assertIn("max_crps", daily)
        self.assertTrue(np.isfinite(list(daily.values())).all())


if __name__ == "__main__":
    unittest.main()

