# Included result snapshot

This directory contains the compact tables needed to audit the numerical claims in the dissertation:

- `primary/metrics/`: aggregate model scores, paired year-block comparisons, horizon-specific coverage, and atypical-day diagnostics.
- `primary/diagnostics/`: all multistart optimisation summaries.
- `primary/provenance/`: frozen configuration, data audit, and software environment.
- `validation/`: exact-file reproducibility comparison, FDR-adjusted sign-flip tests, coverage intervals, and the validation report.
- `sensitivity_alt_mean/` and `sensitivity_utc_origin/`: the same compact metric, diagnostic, and provenance subset for the two revision-stage sensitivity analyses.

Large generated `day_level_scores.csv` and `horizon_level_scores.csv` files are not committed. They can be reconstructed with the frozen configurations. No raw ERA5-Land data are included.

Machine-specific absolute paths in the copied provenance snapshot were replaced with repository-relative paths or `<local-python-3.12>`; numerical values and checksums were not altered.

The archived primary audit uses `source_rows` for the 753,888 rows retained through 2025. The released loader makes the distinction explicit: the frozen CSV contains 758,736 source rows, of which 753,888 fall within the prospective 1940--2025 analysis scope. This labelling clarification does not change any fitted observation, score, or checksum.
