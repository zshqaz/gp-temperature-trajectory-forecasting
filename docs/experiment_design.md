# Experiment design

This document describes the prospective design implemented by the source code. It contains no fitted values or empirical results.

## Forecasting task

Each complete July day is represented by a temperature vector on the common hourly grid 00:00--23:00. At the forecast origin, hours 00:00--09:00 are observed. The model returns a joint predictive distribution for hours 10:00--23:00. The primary object is the complete future trajectory; the post-09:00 maximum is calculated from each joint predictive draw rather than forecast by a separate model.

## Data scope and leakage control

The source is ERA5-Land hourly 2 m temperature at latitude 51.5 and longitude 0.0. The frozen analysis uses July 1940--2025. For a test year `y`, every transformation and model is fitted using years strictly earlier than `y`; all days in year `y` are then held out. This expanding-window design is repeated for 2001--2025.

The loader checks the file hash, required columns, coordinates, missing values, UTC timestamp duplication and completeness of the 24-hour daily curves. Civil-time duplicate hours are collapsed by the pre-specified arithmetic-mean rule. Rows after the configured final year are excluded before summaries or fitted preprocessing.

## Mean and residual process

The mean combines 24 hour indicators with a smooth calendar-year basis. A cyclic second-difference penalty regularises the hour profile, while a separate penalty controls the nonlinear year terms. This mean is re-estimated inside each training fold. Kernels are fitted to the resulting residual curves, so apparent periodicity in the raw diurnal mean is not automatically attributed to residual covariance.

## Gaussian-process candidates

Six covariance specifications are compared under the same mean, folds, optimiser budget and posterior simulation count:

1. squared exponential;
2. Matérn-3/2;
3. Matérn-5/2;
4. exact 24-hour periodic;
5. locally periodic, formed by multiplying periodic and Matérn-3/2 components;
6. additive periodic plus Matérn-3/2.

The period is fixed at 24 hours. Process variances, length scales and the observational nugget are estimated by replicated-curve maximum likelihood on the log scale. Each fold and kernel uses multiple seeded starts of the same bounded pattern-search optimiser. Every start is retained in the diagnostic output, including convergence and boundary indicators.

## Conditioning and joint simulation

For observed residuals `r_O`, the conditional future mean and covariance are

```text
E[r_F | r_O] = K_FO K_OO^{-1} r_O
Var[r_F | r_O] = K_FF - K_FO K_OO^{-1} K_OF.
```

The fold-specific mean is added back to the conditional residual mean. Seeded multivariate-normal draws preserve dependence across future hours and support simultaneous bands, joint scores and maximum-temperature uncertainty.

## Baselines

Three comparison models use the identical training folds and information set:

- persistence with learned future offsets and residual covariance;
- weighted nearest-analogue resampling based on standardised morning residuals;
- multivariate functional ridge regression from the observed residual vector to the future residual vector.

These baselines distinguish the value of Gaussian-process covariance modelling from the more general value of using the morning curve.

## Evaluation

The generated trajectory draws are evaluated at three levels:

- marginal: hourly negative log predictive density, CRPS, PIT values and central interval coverage;
- joint trajectory: energy score, variogram score and simultaneous-band coverage;
- derived maximum: CRPS, absolute error, bias and interval coverage for the draw-wise maximum.

Paired model differences are aggregated by held-out year before resampling. Additional descriptive strata identify upper-tail days, rapid changes and unusual mornings using thresholds estimated from the relevant training fold only.

## Sensitivity configurations

- `configs/sensitivity_alt_mean_v1.json` removes the spline knots and year penalty, leaving a global cubic year basis.
- `configs/sensitivity_utc_origin_v1.json` constructs the same hourly information and target windows in UTC.
- `configs/confirmatory_integrity_v2.yaml` repeats the primary substantive settings in a distinct output directory for deterministic comparison.

Sensitivity analyses change only their named design component. They should not be treated as additional kernel searches.

## Interpretation safeguards

Kernel ranking requires proper-score evidence, calibration evidence and numerical diagnostics to be considered together. A lower average score does not by itself establish reliable superiority when optimisation fails or parameters repeatedly hit bounds. Likewise, marginal interval calibration does not establish simultaneous-path or maximum calibration. External validity is limited to the configured location, month, forecast origin, reanalysis product and evaluation era.
