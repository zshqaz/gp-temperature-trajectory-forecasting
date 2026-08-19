# Source-code walkthrough

This document maps the statistical workflow to the Python implementation. The repository contains the complete executable source; it does not contain cached fits or result tables.

## Execution flow

The command

```bash
python -m gp_temperature_experiment run --config configs/confirmatory.yaml
```

follows this call sequence:

```text
__main__.py
  -> config.load_config
  -> runner.run_experiment
       -> data.load_july_curves
       -> mean.SmoothMeanModel.fit
       -> optimize.fit_kernel
            -> kernels.parameter_bounds
            -> optimize.replicated_gp_nll
            -> kernels.covariance
       -> models.make_gp_conditioner
       -> baseline fitting in models.py
       -> scores.evaluate_forecast
       -> scores.paired_comparisons
       -> checkpoint, provenance and summary writers
```

Each held-out year is processed independently. Training data are selected first, then the mean, kernels and baselines are fitted only on earlier years. The held-out year is never used to construct the mean, parameter bounds, analogue standardisation, regression coefficients or atypical-day thresholds.

## Module responsibilities

| Module | Main responsibility |
|---|---|
| `__main__.py` | Command-line parser and nonzero exit handling |
| `config.py` | Load JSON-compatible configuration files and reject invalid forecast windows or budgets |
| `data.py` | Check the source file and construct complete 24-hour July curves |
| `mean.py` | Fit and predict the penalised hour-plus-year mean function |
| `kernels.py` | Define kernel parameters, bounds and covariance matrices |
| `optimize.py` | Evaluate replicated-curve GP likelihoods and perform seeded multistart optimisation |
| `models.py` | Condition fitted GPs, generate joint draws and fit three probabilistic baselines |
| `scores.py` | Calculate marginal, joint, maximum and coverage diagnostics |
| `runner.py` | Orchestrate rolling folds, checkpoint outputs and record provenance |
| `validation.py` | Compare deterministic reruns and perform year-block statistical validation |

## Data construction (`data.py`)

`load_july_curves` is the input gate. It confirms that the requested file exists, reads only `valid_time`, `t2m`, `latitude` and `longitude`, confirms the single grid point, converts Kelvin to Celsius and constructs a date-by-hour matrix. For local civil time, repeated clock-hour cells are averaged according to the frozen policy. Any incomplete day, unexpected coordinate, missing value or duplicate UTC timestamp raises an exception. File naming and CSV serialization do not affect acceptance when the parsed content is valid.

The return value contains both the curve matrix and a machine-readable audit dictionary. The audit is written to each run's provenance directory.

## Mean model (`mean.py`)

`SmoothMeanModel` uses 24 hour indicators and a truncated cubic year basis. Its design matrix is estimated by penalised least squares. The hour penalty uses a cyclic second-difference operator, ensuring that the end and start of the clock are adjacent for smoothing purposes. Calendar-year terms have their own penalty and can be changed through configuration.

`fit` stores only coefficients and basis metadata. `predict_curves` constructs a 24-hour mean for every requested year. The runner subtracts these predictions before estimating residual covariance.

## Covariance kernels (`kernels.py`)

`SPECS` is the authoritative parameter inventory. All positive parameters are represented on the log scale. `parameter_bounds` ties variance and nugget ranges to the training residual variance and supplies common length-scale bounds.

`covariance` implements squared exponential, Matérn-3/2, Matérn-5/2, exact periodic, locally periodic and additive covariance. The periodic component fixes the period at 24 hours. A nugget is added only to square self-covariance matrices; cross-covariances never receive a nugget.

## Likelihood optimisation (`optimize.py`)

For replicated zero-mean residual curves `R`, `replicated_gp_nll` evaluates the Gaussian negative log likelihood from the scatter matrix `R.T @ R`. Cholesky factorisation provides the log determinant and quadratic term without explicitly forming a matrix inverse.

`fit_kernel` creates one midpoint start and seeded random starts inside the bounds. `_pattern_search` explores positive and negative coordinate directions, shrinks the step after unsuccessful sweeps and stops under the configured tolerance or evaluation budget. The best finite objective is returned, while diagnostics for every start preserve the objective, convergence flag, evaluation count, boundary flag and parameter vector.

## Forecast models (`models.py`)

`make_gp_conditioner` partitions the fitted covariance into observed and future blocks. It solves linear systems for the conditional gain and regularises the Schur-complement covariance before sampling. `GPConditioner.forecast` adds the conditional residual correction to the future mean and draws complete future paths.

The comparison models are deliberately probabilistic:

- `PersistenceBaseline` learns the mean future offset from the 09:00 temperature and the covariance of its training errors.
- `AnalogBaseline` finds nearby standardised morning residual curves and resamples their future residual paths using distance weights.
- `FunctionalRidgeBaseline` estimates a regularised multivariate map from the ten observed residual hours to the fourteen future residual hours and samples from its residual covariance.

`gaussian_samples` first attempts Cholesky simulation and falls back to an eigenvalue-clipped factorisation if numerical roundoff prevents decomposition.

## Scores (`scores.py`)

`evaluate_forecast` accepts the observed fourteen-hour vector and a matrix of joint predictive draws. It produces:

- per-hour NLPD, ensemble CRPS, PIT, standardised residuals and central intervals;
- daily energy and variogram scores for the trajectory;
- draw-calibrated simultaneous bands;
- CRPS, bias, error and interval coverage for the draw-wise maximum.

`paired_comparisons` computes candidate-minus-reference loss differences and resamples held-out-year means, preserving the annual blocking used by the evaluation design.

## Orchestration and generated output (`runner.py`)

`ExperimentRunner` creates output subdirectories, records a JSON-lines progress log and writes the frozen configuration, environment and data audit. After every fold it checkpoints the granular score tables, limiting loss if a long run is interrupted. Final summary tables are derived from the accumulated day- and horizon-level rows.

Random seeds are deterministic functions of the configured seed, held-out year, day and model index. This makes posterior simulation reproducible without sharing precomputed predictions.

## Validation (`validation.py`)

The validation module takes two independently generated run directories. It compares corresponding files byte-for-byte, applies paired sign-flip tests to year-level score differences, adjusts the resulting p-values with Benjamini--Hochberg, and constructs year-block bootstrap intervals for coverage. It never imports a bundled result snapshot.

## Extending the project

To add a kernel, register its parameter names in `SPECS`, add bounds in `parameter_bounds`, implement its covariance branch, include it in a configuration, and add a positive-definiteness test. To add a forecast model, implement a fitted object with a `forecast` method returning a mean and joint draws, fit it inside each runner fold, and add a deterministic test. New metrics should be calculated from the same held-out observations and joint draws inside `scores.py`; avoid reading summary files back into the forecasting pipeline.
