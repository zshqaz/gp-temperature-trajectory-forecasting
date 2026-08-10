# Stage 4 Revision Experiment Protocol

Protocol frozen: 2026-08-05
Source code: `gp_temperature_experiment/`
Base evidence: Stage 2.5 integrity-verified confirmatory run
Roadmap target: R1 and R2

## Scope decision

The existing user-owned code exposes mean-model and timezone choices through configuration but does not implement an independent second optimiser or a rolling training window. Experiment Agent rules prohibit silently generating or modifying the user's experiment scripts. Therefore:

- **R1:** the manuscript will follow the roadmap's permitted fallback and reclassify additive-kernel rankings as exploratory unless independently optimised evidence is later supplied. Existing non-convergence evidence remains unchanged.
- **R2:** two full sensitivity runs will be executed with the existing verified pipeline: an alternative mean model and a UTC forecast-origin specification.

## Sensitivity A — alternative mean model

- Configuration: `configs/sensitivity_alt_mean_v1.json`
- Change from primary: the four-knot penalised year spline is replaced by an unpenalised global cubic year basis (`year_knots=0`, `year_smoothing=0`); the cyclic hour penalty, local-time target, kernels, baselines, folds, seeds and scores remain unchanged.
- Purpose: test whether kernel rankings and calibration depend on the primary year-mean flexibility.

## Sensitivity B — UTC origin

- Configuration: `configs/sensitivity_utc_origin_v1.json`
- Change from primary: curves are constructed in UTC and the information set is 00:00–09:00 UTC with target 10:00–23:00 UTC; all other primary settings remain unchanged.
- Purpose: test whether the one-hour summer clock shift materially changes the ranking and calibration conclusions.

## Exact commands awaiting execution confirmation

Working directory for both commands: repository root.

1. `python -m gp_temperature_experiment run --config configs/sensitivity_alt_mean_v1.json`
2. `python -m gp_temperature_experiment run --config configs/sensitivity_utc_origin_v1.json`

## Monitoring and success criteria

- Type: analysis and simulation.
- External hard timeout: 30 minutes per process; internal timeout: 1 hour.
- Monitor files: each run's `logs/progress.jsonl` and output-directory growth.
- Success: exit code 0; complete metric, optimisation, provenance and result files; 775 held-out days and nine models; no missing primary output.
- Anomaly rule: no output change for 90 seconds is advisory only; crashes are reported without automatic retry.

## Planned validation

After both runs finish, the validation stage will compare the two sensitivity summaries with the frozen primary run, inspect fold-level optimisation, recompute headline contrasts, check all 11 statistical fallacy types, and issue `VERIFIED` only if deterministic reruns or appropriate artifact comparisons support it.
