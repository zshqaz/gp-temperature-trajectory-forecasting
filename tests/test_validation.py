from __future__ import annotations

import unittest

import numpy as np

from gp_temperature_experiment.validation import benjamini_hochberg


class ValidationTests(unittest.TestCase):
    def test_bh_adjustment_is_monotone_in_rank(self) -> None:
        values = np.array([0.04, 0.001, 0.02, 0.5])
        adjusted = benjamini_hochberg(values)
        order = np.argsort(values)
        self.assertTrue(np.all(np.diff(adjusted[order]) >= -1e-12))
        self.assertTrue(np.all(adjusted >= values))
        self.assertTrue(np.all(adjusted <= 1.0))


if __name__ == "__main__":
    unittest.main()

