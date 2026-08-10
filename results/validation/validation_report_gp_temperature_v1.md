## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: 2026-07-28T15:43:53+01:00
- Verification Status: VERIFIED
- Version Label: validation_v1
- Integrity Pass Date: 2026-07-28T15:43:53+01:00
- Upstream Dependencies:
  - exp_result_v1
  - code_plan_v1
  - research_v1.1-provenance-resolved

## Validation Report

- **Source**: exp-kernel-comparison
- **Overall Confidence**: CAUTION
- **Reproducibility**: REPRODUCIBLE
- **Statistical fallacy coverage**: 11/11 checked
- **Scope**: descriptive interpretation of the experiment outputs; no editorial recommendation about dissertation wording is made.

The numeric pipeline is internally complete and exactly reproducible. The main caution is substantive rather than computational: every confirmatory GP is undercalibrated to some degree, the additive kernel's apparent score advantage is entangled with 12 fold-level non-convergence events, and atypical-day strata—especially the 20 rapid-change days—show severe undercoverage.

### Statistical Findings

All score differences are candidate minus Matérn-3/2, so negative values favor the candidate. Confidence intervals are 95% year-block bootstrap intervals over 25 test years. FDR values come from 10,000 year-level paired sign-flip replicates with Benjamini–Hochberg correction across all 40 comparisons.

| Finding | Estimate and uncertainty | Relative effect | Confidence |
|---|---|---:|---|
| Additive GP marginal NLPD | −0.1225, CI [−0.1570, −0.0884], FDR p = 0.00013 | 6.0% lower | CAUTION |
| Additive GP marginal CRPS | −0.1559, CI [−0.1961, −0.1192], FDR p = 0.00013 | 13.9% lower | CAUTION |
| Additive GP energy score | −0.6265, CI [−0.7896, −0.4787], FDR p = 0.00013 | 13.2% lower | CAUTION |
| Additive GP variogram score | −0.00468, CI [−0.00699, −0.00254], FDR p = 0.00077 | 3.3% lower | CAUTION |
| Additive GP maximum CRPS | −0.1432, CI [−0.1810, −0.1068], FDR p = 0.00013 | 11.8% lower | CAUTION |
| Locally periodic GP marginal CRPS | +0.00172, CI [+0.00040, +0.00310], FDR p = 0.0257 | 0.15% higher | CAUTION |
| Matérn-5/2 GP marginal CRPS | +0.1009, CI [+0.0861, +0.1175], FDR p = 0.00013 | 9.0% higher | SOLID |
| Periodic GP marginal NLPD | +0.1758, CI [+0.1141, +0.2442], FDR p = 0.00013 | 8.6% higher | SOLID |
| Periodic GP variogram score | +0.02408, CI [+0.02064, +0.02805], FDR p = 0.00013 | 17.2% higher | SOLID |
| Squared-exponential GP marginal CRPS | +0.2878, CI [+0.2466, +0.3341], FDR p = 0.00013 | 25.6% higher | SOLID |
| Functional baseline marginal CRPS | −0.2940, CI [−0.3586, −0.2345], FDR p = 0.00013 | 26.2% lower | SOLID |
| Functional baseline energy score | −1.1835, CI [−1.4341, −0.9490], FDR p = 0.00013 | 25.0% lower | SOLID |

The additive GP has the best average scores among the six GP kernels and its paired differences favor it in 84%–100% of test years, depending on metric. It does not satisfy the frozen practical-superiority declaration because 12 of its 25 fold-level fits had no start meeting the convergence rule. This is a pre-specified disqualifying condition even though the score intervals exclude zero.

The locally periodic and Matérn-3/2 kernels are numerically close. The locally periodic differences in NLPD, CRPS, and energy survive FDR correction but are only about 0.10%–0.17% of the Matérn-3/2 means; maximum CRPS and variogram differences do not survive FDR correction.

The functional baseline has the lowest average NLPD, CRPS, energy score, variogram score, and maximum CRPS among all nine evaluated models. This is a descriptive comparison, not a claim that it is universally superior outside the frozen test population.

### Calibration Findings

Year-block intervals show that undercoverage is not confined to one test year.

| Model and target | Nominal | Estimated coverage | 95% year-block CI | Assessment |
|---|---:|---:|---:|---|
| Additive GP, marginal | 80% | 76.5% | [73.8%, 79.0%] | Undercoverage |
| Additive GP, marginal | 95% | 92.4% | [90.9%, 93.8%] | Undercoverage |
| Additive GP, simultaneous trajectory | 95% | 90.8% | [88.3%, 93.2%] | Undercoverage |
| Additive GP, future maximum | 95% | 90.7% | [88.4%, 93.0%] | Undercoverage |
| Matérn-3/2 GP, marginal | 80% | 76.2% | [73.0%, 79.2%] | Undercoverage |
| Matérn-3/2 GP, marginal | 95% | 92.8% | [90.7%, 94.6%] | Undercoverage |
| Matérn-3/2 GP, simultaneous trajectory | 95% | 92.4% | [90.1%, 94.5%] | Undercoverage |
| Matérn-3/2 GP, future maximum | 95% | 90.3% | [87.4%, 93.0%] | Undercoverage |
| Periodic GP, simultaneous trajectory | 95% | 71.0% | [67.4%, 74.7%] | Severe undercoverage |
| Squared-exponential GP, future maximum | 95% | 81.9% | [77.8%, 85.9%] | Severe undercoverage |
| Functional baseline, simultaneous trajectory | 95% | 95.5% | [93.5%, 97.2%] | Compatible with nominal |
| Functional baseline, future maximum | 95% | 97.5% | [96.6%, 98.5%] | Conservative coverage |

Mean PIT and standardized residual values for the GP models are near their central targets, while coverage is low. The observed pattern is therefore more consistent with underdispersion or dependence misspecification than with a large overall location bias.

### Atypical-Day Findings

The frozen test strata contain 72 upper-tail days, 20 rapid-change days, and 30 unusual-morning days.

| Stratum | Model | CRPS | 80% simultaneous coverage | 95% simultaneous coverage | 95% maximum coverage |
|---|---|---:|---:|---:|---:|
| Upper-tail | Additive GP | 1.850 | 37.5% | 70.8% | 61.1% |
| Upper-tail | Matérn-3/2 GP | 2.348 | 30.6% | 65.3% | 45.8% |
| Upper-tail | Functional baseline | 0.944 | 79.2% | 95.8% | 94.4% |
| Rapid-change | Additive GP | 2.336 | 20.0% | 50.0% | 40.0% |
| Rapid-change | Matérn-3/2 GP | 2.699 | 25.0% | 55.0% | 35.0% |
| Rapid-change | Functional baseline | 1.206 | 70.0% | 90.0% | 85.0% |
| Unusual morning | Additive GP | 1.607 | 60.0% | 73.3% | 66.7% |
| Unusual morning | Matérn-3/2 GP | 1.743 | 66.7% | 76.7% | 70.0% |
| Unusual morning | Functional baseline | 0.947 | 73.3% | 96.7% | 90.0% |

The rapid-change estimates have substantial sampling uncertainty because only 20 test days meet that training-defined criterion. The direction and magnitude nevertheless show that overall-average calibration does not describe performance on these paths.

### Multiple Comparisons

- Total paired tests: 40.
- FDR procedure: Benjamini–Hochberg at q = 0.05.
- Tests surviving FDR correction: 36/40.
- Non-surviving comparisons:
  - locally periodic versus Matérn-3/2 for maximum CRPS;
  - locally periodic versus Matérn-3/2 for variogram score;
  - periodic versus Matérn-3/2 for marginal CRPS; and
  - periodic versus Matérn-3/2 for energy score.
- The sign-flip p-values use year-level paired differences and assume their null distribution is approximately symmetric.

### Assumption and Integrity Warnings

| Type | Detail | Affected |
|---|---|---|
| Optimization | 12/25 additive-kernel folds had no converged start; 449/3,000 starts reached a parameter boundary. No retry or manual tuning occurred. | Additive GP effect estimates and practical-superiority declaration |
| Calibration | All six GP models undercovered at important nominal levels; periodic and squared-exponential failures were especially large. | GP uncertainty claims |
| Dependence | Year-block inference has 25 independent resampling blocks; tail quantiles can be imprecise with this block count. | All confidence intervals |
| Monte Carlo | Each forecast uses 5,000 seeded paths; finite-draw uncertainty was not separately propagated into score intervals. | Joint and maximum scores |
| Model assumptions | GP intervals condition on fitted hyperparameters and Gaussian residual structure; hyperparameter and ERA5 reanalysis uncertainty are omitted. | All GP predictive intervals |
| Historical clock | The repeated local 02:00 during the 1945-07-15 double-summer-time transition was collapsed by a pre-recorded mean rule. | One training curve |
| Sensitivities | The primary run is complete, but the planned UTC-origin, rolling-window, alternative-mean, and historical-block sensitivities were not run. | Robustness beyond the primary design |

### Fallacy Scan

- **Coverage**: 11/11 fallacy types checked.

| Fallacy | Severity | Finding | Safeguard/status |
|---|---|---|---|
| 1. Simpson's paradox | NOTE | No aggregate reversal was detected. Additive-GP score improvements occur in 84%–100% of test years, depending on metric. Periodic results are heterogeneous but not an all-strata reversal. | Year fractions and block intervals reported. |
| 2. Ecological fallacy | NOTE | Unit of analysis and inference are both July-day trajectories at one ERA5 grid point. No person- or neighborhood-level inference is supported. | Inference remains at the reanalysis grid-point/day level. |
| 3. Berkson's paradox | NOTE | Days are selected by month and completeness, matching the target population rather than by joint predictor/outcome status. | No outcome-conditioned sample selection was used for the primary analysis. |
| 4. Collider bias | NOTE | No causal adjustment set is fitted. Conditioning on the morning prefix defines the forecast information set rather than a causal control strategy. | No causal coefficient interpretation is made. |
| 5. Base-rate neglect | NOTE | This is not a diagnostic-classification study. Atypical-day base counts are explicitly reported: 72, 20, and 30. | Stratum sizes accompany all diagnostic results. |
| 6. Regression to the mean | NOTE | Upper-tail and rapid-change strata are selected retrospectively by held-out outcomes, but no pre/post improvement claim is made. | Strata are treated only as failure diagnostics. |
| 7. Survivorship bias | NOTE | All 775 held-out July days were scored; there was no test-set attrition or complete-case filtering after prediction. | Record counts and keys were verified. |
| 8. Look-elsewhere effect | NOTE | All 40 frozen comparisons are retained, including null and adverse results; 36 survive BH FDR. | Full comparison table is preserved. |
| 9. Garden of forking paths | CAUTION | The primary configuration was frozen before the confirmatory run, but several planned sensitivity analyses remain unexecuted and the 1945 clock rule was added after a smoke-test gate failure. | Deviations are disclosed; primary results are not redefined using sensitivity outcomes. |
| 10. Correlation is not causation | NOTE | Results compare predictive algorithms on the same held-out series. They do not show that kernels cause physical temperature behavior or operational weather outcomes. | Claims remain predictive and comparative. |
| 11. Reverse causality | NOTE | The observed prefix temporally precedes the withheld suffix; no directional causal claim is made. | Not detected under the stated predictive scope. |

### Reproducibility

- **Method**: deterministic re-run using identical data hash, code, configuration, seeds, runtime, and command.
- **Original duration**: 105.969 seconds.
- **Re-run duration**: 107.953 seconds; timing is excluded from deterministic content comparison.
- **Verdict**: REPRODUCIBLE.

| Artifact class | Files | Comparison | Status |
|---|---:|---|---|
| Metric CSVs | 6 | SHA-256 byte-for-byte | MATCH |
| Optimization diagnostics | 1 | SHA-256 byte-for-byte | MATCH |
| Frozen configuration | 1 | SHA-256 byte-for-byte | MATCH |
| Data audit | 1 | SHA-256 byte-for-byte | MATCH |
| Environment record | 1 | SHA-256 byte-for-byte | MATCH |

All 10 critical files matched exactly. The timestamped Markdown result and progress log were excluded because their timestamps, elapsed time, and accumulated monitoring history necessarily change between runs.

### Verification Verdict

The experiment is execution-reproducible and the reported paired score differences are supported by dependence-aware intervals and multiplicity control. Verification does not remove the substantive cautions: the additive kernel fails the frozen optimizer-stability condition, GP uncertainty is generally undercalibrated, and atypical-day coverage is poor. Accordingly, the artifact is marked **VERIFIED** with **Overall Confidence: CAUTION**.
