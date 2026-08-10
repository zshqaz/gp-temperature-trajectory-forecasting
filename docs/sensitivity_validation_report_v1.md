# Stage 4 Sensitivity Validation Report

## Material Passport

- Origin Skill: experiment-agent
- Origin Mode: validate
- Origin Date: 2026-08-05
- Verification Status: ANALYZED
- Version Label: sensitivity_validation_v1
- Overall Confidence: CAUTION

The two pre-specified Stage 4 sensitivity runs completed successfully and passed structural output checks. The primary experiment remains integrity-verified by its earlier deterministic rerun. The two new sensitivity artifacts are classified as **ANALYZED**, rather than VERIFIED, because no byte-for-byte rerun of either new configuration has yet been authorised or completed.

## 1. Executed analyses

| Analysis | Deliberate change from primary | Exit code | Duration (s) | Test days | Models | Draws per forecast |
|---|---|---:|---:|---:|---:|---:|
| Alternative mean | Four-knot penalised year spline replaced by an unpenalised global cubic year basis (`year_knots=0`, `year_smoothing=0`) | 0 | 153.735 | 775 | 9 | 5,000 |
| UTC origin | Curves and the 09:00 forecast origin defined in UTC rather than Europe/London local time | 0 | 151.688 | 775 | 9 | 5,000 |

Both analyses used the same ERA5 hourly time-series input (SHA-256 `159bdc3a41b80e161c3190a56601bfaa414f4c2137289193e8fc506626cc4441`), the same 2001–2025 expanding-window test years, six GP kernels, three probabilistic baselines, optimisation budget, forecast scores and seeds as the primary experiment.

## 2. Structural integrity checks

Each run produced all required artifacts: 9 model-summary rows, 6,975 day-level rows, 97,650 horizon-level rows, 40 paired-comparison rows, 126 horizon-coverage rows, 27 atypical-day rows and 3,000 optimisation-start rows. The data gates reported 2,666 complete July curves, 63,984 in-scope hourly observations, no duplicate source timestamps and no missing 2 m temperatures. Both processes ended with `run_completed` and exit code 0.

Key output hashes:

| Artifact | SHA-256 |
|---|---|
| Alternative-mean model summary | `AE215EE7919E17C4D5D2F3E11355F4051F99D6D0658B08AE74C0E054F78C8B6D` |
| UTC-origin model summary | `172CF5608C1601030B6D84E90460C90747060401A3F872127A4A824E5EB1E113` |
| Alternative-mean frozen configuration | `54178FBBFE962715EF1827EDAC467A573F4787B790D358EC0DDD8301EEE2BC80` |
| UTC-origin frozen configuration | `9C1BB07191C45F4B4D178FDBF3628184E32EE2A0F514F32035067F5574A7A873` |

## 3. Headline results

Lower scores are better. Coverage entries are empirical proportions for nominal 95% simultaneous trajectory bands and 95% maximum-temperature intervals.

| Analysis | Model | NLPD | CRPS | Energy | Variogram | Maximum CRPS | Simultaneous 95% | Maximum 95% |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Primary | Functional ridge | 1.7720 | 0.8283 | 3.5481 | 0.1207 | 0.8729 | 0.955 | 0.975 |
| Primary | Additive GP | 1.9278 | 0.9664 | 4.1050 | 0.1353 | 1.0675 | 0.908 | 0.907 |
| Primary | Matérn-3/2 GP | 2.0504 | 1.1222 | 4.7316 | 0.1400 | 1.2108 | 0.924 | 0.903 |
| Primary | Locally periodic GP | 2.0524 | 1.1240 | 4.7398 | 0.1401 | 1.2118 | 0.924 | 0.902 |
| Primary | Periodic GP | 2.2261 | 1.1319 | 4.8089 | 0.1640 | 1.2741 | 0.710 | 0.884 |
| Alternative mean | Functional ridge | 1.7712 | 0.8273 | 3.5428 | 0.1203 | 0.8734 | 0.955 | 0.975 |
| Alternative mean | Additive GP | 1.9213 | 0.9602 | 4.0813 | 0.1351 | 1.0583 | 0.911 | 0.912 |
| Alternative mean | Matérn-3/2 GP | 2.0250 | 1.0918 | 4.6078 | 0.1385 | 1.1780 | 0.924 | 0.911 |
| Alternative mean | Locally periodic GP | 2.0271 | 1.0933 | 4.6150 | 0.1386 | 1.1786 | 0.928 | 0.908 |
| Alternative mean | Periodic GP | 2.2087 | 1.1155 | 4.7426 | 0.1623 | 1.2441 | 0.714 | 0.902 |
| UTC origin | Functional ridge | 1.7316 | 0.7826 | 3.3556 | 0.1171 | 0.7646 | 0.955 | 0.963 |
| UTC origin | Additive GP | 1.8927 | 0.9105 | 3.8635 | 0.1276 | 0.9257 | 0.893 | 0.917 |
| UTC origin | Matérn-3/2 GP | 2.0172 | 1.0552 | 4.4375 | 0.1295 | 1.0333 | 0.912 | 0.919 |
| UTC origin | Locally periodic GP | 2.0198 | 1.0576 | 4.4486 | 0.1297 | 1.0349 | 0.914 | 0.919 |
| UTC origin | Periodic GP | 2.1967 | 1.0999 | 4.6591 | 0.1568 | 1.1339 | 0.721 | 0.906 |

## 4. Interpretation against the revision questions

### 4.1 Alternative mean function

Changing the year component of the mean made only small changes to the principal hierarchy. Relative to the primary analysis, Matérn-3/2 NLPD improved by 0.0254 and CRPS by 0.0304; its 95% simultaneous coverage stayed at 0.924 and maximum coverage increased from 0.903 to 0.911. Locally periodic covariance remained effectively tied with Matérn-3/2 (paired mean difference: NLPD 0.0021, 95% year-block bootstrap interval [0.0007, 0.0036]; CRPS 0.0015 [0.0001, 0.0031]). Exact periodic covariance remained materially worse in NLPD, variogram score and simultaneous calibration. The substantive stable-kernel conclusion is therefore robust to this change in centring.

### 4.2 UTC forecast origin

Defining curves in UTC improved average scores for most methods but did not reverse the model hierarchy. Matérn-3/2 NLPD improved by 0.0332 and CRPS by 0.0671 relative to the primary local-time analysis. Locally periodic remained slightly worse than Matérn-3/2 (NLPD difference 0.0026 [0.0012, 0.0041]; CRPS difference 0.0025 [0.0012, 0.0040]). Functional ridge again remained best overall. However, Matérn-3/2 simultaneous 80% coverage fell from 0.787 to 0.743 and 95% simultaneous coverage from 0.924 to 0.912, despite better average scores. This is a genuine accuracy–calibration trade-off and rules out treating the clock change as a uniform improvement.

### 4.3 Strong baselines

The functional baseline beat Matérn-3/2 in every analysis. Its paired annual NLPD advantage was −0.2783 in the primary analysis (95% interval [−0.3431, −0.2207]), −0.2538 under the alternative mean ([−0.3160, −0.1975]) and −0.2856 under UTC ([−0.3313, −0.2439]). The corresponding CRPS intervals also excluded zero in all three analyses. This establishes a robust experiment-specific hierarchy: functional ridge is best overall; Matérn-3/2 is the most credible stable GP reference.

### 4.4 Additive covariance

Additive covariance retained the best observed average GP scores. Against Matérn-3/2, its annual mean CRPS difference was −0.1559 in the primary analysis, −0.1317 under the alternative mean and −0.1446 under UTC; all three 95% year-block intervals excluded zero. These are descriptive predictive gains, not confirmatory superiority, because the numerical identification failure persisted. The selected additive fit met the convergence rule in only 13/25 primary folds and 16/25 folds in each sensitivity analysis. Across all 500 starts, only 17, 22 and 27 starts converged, respectively. No independent optimiser was available in the frozen user-owned code. In accordance with the pre-specified fallback, additive results must be labelled **exploratory** throughout the revised manuscript.

### 4.5 Atypical days

Sensitivity analyses did not remove the failure on difficult regimes. Under the alternative mean, Matérn-3/2 simultaneous 95% coverage was 0.667 on upper-tail days and 0.500 on rapid-change days; under UTC it was 0.736 and 0.500. Functional ridge was stronger but imperfect, with corresponding UTC coverages of 0.931 and 0.900. These small-stratum diagnostics are descriptive and should not be interpreted as causal evidence about weather regimes.

## 5. Robustness classification

| Claim | Classification | Evidence |
|---|---|---|
| Functional ridge is the best model in this experiment | Robust | Lowest headline scores in primary, alternative-mean and UTC analyses; paired intervals versus Matérn-3/2 exclude zero |
| Matérn-3/2 is the most credible stable GP reference | Robust | Best or near-best stable-GP scores; 25/25 selected fits converged in every analysis |
| Locally periodic covariance materially improves on Matérn-3/2 | Not supported | Differences remain approximately 0.002 and favour Matérn-3/2; locally periodic starts frequently hit bounds |
| Exact periodic covariance is adequate after mean removal | Not supported | Persistently worse density/dependence scores and 95% simultaneous coverage of 0.710–0.721 |
| Additive covariance is the superior GP | Unresolved / exploratory | Better observed scores but persistent non-convergence and no independent optimiser verification |
| Better average proper scores imply better calibration | Rejected | UTC improves scores while lowering Matérn-3/2 simultaneous coverage |
| Results transfer beyond one July grid-point reanalysis task | Unresolved | No spatial, seasonal or observational-station validation |

## 6. Statistical interpretation and fallacy audit

1. **Statistical versus practical significance:** paired intervals are reported with effect sizes; tiny locally periodic differences are not promoted as practically meaningful.
2. **Multiple comparisons:** the sensitivity analyses are robustness checks, not a new search for isolated significant contrasts; the frozen primary multiplicity procedure remains authoritative.
3. **Correlation versus causation:** no causal effect of kernel choice on physical weather is claimed.
4. **P-value misinterpretation:** bootstrap intervals and year-favouring fractions describe predictive-loss differences; they do not give the probability that a model is true.
5. **Confidence-interval misinterpretation:** intervals quantify repeated-sample uncertainty under the year-block procedure, not a posterior probability for the fixed interval.
6. **Base-rate neglect:** difficult-day strata and sample sizes remain explicit; rare heat and rapid-change cases are not treated as representative of all days.
7. **Regression to the mean:** no improvement is inferred from selecting extreme days and then observing subsequent moderation.
8. **Survivorship bias:** all test years, all nine models and failed optimisation starts remain in the audit.
9. **Ecological fallacy:** grid-point aggregate evidence is not assigned to individual stations, residents or all UK locations.
10. **Simpson's paradox:** overall and atypical-stratum results are both reported; no pooled claim is used to conceal subgroup deterioration.
11. **Overfitting:** preprocessing is fold-specific and training-only; sensitivity choices were frozen before viewing their results. The unresolved additive optimiser remains an explicit risk rather than being selected as confirmatory on held-out scores.

## 7. Limitations and verification status

The alternative mean is a meaningful but single centring perturbation; it does not exhaust plausible nonstationary means. UTC is a clock-origin sensitivity, not a rolling-window climate-regime analysis. Both analyses reuse the same deterministic implementation, so they cannot independently validate its algorithms. The additive kernel has not been checked with a second optimiser. Finally, the new output artifacts have not undergone a deterministic duplicate run and therefore remain ANALYZED. These limitations constrain generalisation but do not negate the observed robustness of the stable-kernel and baseline hierarchy.

## 8. Manuscript decision

The revised dissertation should: (i) retain the primary numerical results unchanged; (ii) add this compact sensitivity evidence; (iii) demote additive performance to exploratory in the Abstract, Results, Discussion and Conclusion; (iv) state the four-level contribution hierarchy consistently; and (v) distinguish kernel-relative calibration differences from undercoverage mechanisms shared by all tested GPs.
