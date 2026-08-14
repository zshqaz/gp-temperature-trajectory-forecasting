# Configuration reference

Configuration files use JSON syntax even when their extension is `.yaml`. This allows them to be loaded by the Python standard library without an additional YAML dependency.

## Top-level keys

| Key | Meaning |
|---|---|
| `experiment_id` | Human-readable experiment family identifier |
| `version_label` | Label written into the frozen run configuration |
| `data_path` | Local path to the separately downloaded ERA5-Land CSV |
| `expected_sha256` | Exact permitted data-file checksum |
| `output_root` | New directory receiving generated artifacts |
| `analysis` | Time scope, clock definition, forecast split and test years |
| `mean_model` | Mean-basis and smoothing settings |
| `kernels` | Ordered list of covariance models to fit |
| `optimization` | Multistart search budget, tolerance and seed |
| `posterior` | Number of joint trajectory draws and seed |
| `baselines` | Analogue and ridge regularisation settings |
| `bootstrap` | Paired-comparison resampling settings |
| `monitoring` | Heartbeat interval and hard timeout |

## `analysis`

- `first_year`, `last_year`: inclusive data range used to build July curves.
- `month`: calendar month selected after timezone conversion.
- `timezone`: IANA timezone used to define the daily curve.
- `local_duplicate_hour_policy`: must be `mean`; this freezes handling of repeated civil hours.
- `observed_hours`: must be hours 0 through 9.
- `future_hours`: must be hours 10 through 23.
- `test_year_start`, `test_year_end`: inclusive held-out evaluation years. Training years are always strictly earlier than the current test year.

## `mean_model`

- `hour_smoothing`: strength of the cyclic second-difference penalty on the 24 hour effects.
- `year_knots`: number of interior knots in the truncated cubic calendar-year basis; zero retains only global cubic terms.
- `year_smoothing`: ridge penalty applied to nonlinear year terms.

## `kernels`

Valid names are `se`, `matern32`, `matern52`, `periodic`, `locally_periodic` and `additive`. Ordering affects only deterministic seed allocation and output order; every listed kernel receives the same optimisation budget.

## `optimization`

- `starts`: number of independent parameter initialisations per fold and kernel.
- `max_evaluations_per_start`: maximum objective evaluations for each start.
- `relative_tolerance`: stopping tolerance used after an unsuccessful search sweep.
- `seed`: base seed for initial-point generation.

## `posterior`

- `draws`: number of joint future trajectories generated for each model-day forecast. At least 20 are required.
- `seed`: base seed combined with year, day and model indices.

## `baselines`

- `analog_k`: number of nearest morning curves eligible for weighted resampling.
- `functional_ridge`: regularisation strength for the morning-to-future multivariate regression.
- `covariance_ridge`: relative diagonal stabiliser used for baseline error covariance matrices.

## `bootstrap`

- `repetitions`: number of resamples for paired year-block intervals.
- `seed`: deterministic resampling seed.
- `reference_model`: model name used as the comparison reference, normally `gp_matern32`.

## `monitoring`

- `heartbeat_seconds`: minimum time between progress heartbeat records.
- `hard_timeout_hours`: internal wall-clock safety limit checked between major operations.

## Included configurations

| File | Intended use |
|---|---|
| `configs/smoke.yaml` | Reduced one-year end-to-end installation check |
| `configs/confirmatory.yaml` | Frozen primary experiment |
| `configs/confirmatory_integrity_v2.yaml` | Same substantive design with a separate output root for deterministic comparison |
| `configs/sensitivity_alt_mean_v1.json` | Alternative calendar-year mean basis |
| `configs/sensitivity_utc_origin_v1.json` | UTC curve and forecast-origin definition |

Before creating a new configuration, copy the nearest existing file and change `experiment_id`, `version_label` and `output_root`. Change substantive settings only when the new run is explicitly intended as a different analysis. Never point two concurrent runs at the same output directory.
