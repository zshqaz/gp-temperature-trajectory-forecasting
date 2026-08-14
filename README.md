# Gaussian-process forecasting of London July temperatures

It studies how covariance-kernel specification affects the predictive accuracy and uncertainty calibration of Gaussian-process models that forecast the remaining London July temperature trajectory after observations through 09:00 local time.

The analysis uses hourly ERA5-Land 2 m temperature at latitude 51.5, longitude 0.0. July days from 1940--2025 are represented as replicated 24-hour curves. Evaluation is rolling-origin by year for 2001--2025. The main probabilistic target is the temperature trajectory from 10:00--23:00; the daily post-09:00 maximum is a secondary derived target.

## What is included

- `gp_temperature_experiment/`: data checks, mean model, covariance kernels, optimisation, posterior prediction, scoring, and validation code.
- `configs/`: frozen confirmatory, integrity, smoke-test, and sensitivity configurations.
- `tests/`: deterministic unit tests.
- `results/`: compact result tables, optimisation diagnostics, provenance, and the deterministic reproducibility comparison used in the dissertation.
- `docs/`: data acquisition, complete reproduction commands, experiment protocol, and validation notes.

The raw ERA5-Land file and large generated day- and horizon-level output tables are not committed. The analysed CSV is identified by SHA-256, and the program refuses to run if the checksum differs.


