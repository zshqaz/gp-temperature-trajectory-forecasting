from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from gp_temperature_experiment.validation import benjamini_hochberg, files_equal


class ValidationTests(unittest.TestCase):
    def test_bh_adjustment_is_monotone_in_rank(self) -> None:
        values = np.array([0.04, 0.001, 0.02, 0.5])
        adjusted = benjamini_hochberg(values)
        order = np.argsort(values)
        self.assertTrue(np.all(np.diff(adjusted[order]) >= -1e-12))
        self.assertTrue(np.all(adjusted >= values))
        self.assertTrue(np.all(adjusted <= 1.0))

    def test_file_comparison_uses_contents_directly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.bin"
            same = root / "same.bin"
            different = root / "different.bin"
            first.write_bytes(b"complete experiment output")
            same.write_bytes(b"complete experiment output")
            different.write_bytes(b"changed experiment output")
            self.assertTrue(files_equal(first, same))
            self.assertFalse(files_equal(first, different))


if __name__ == "__main__":
    unittest.main()
