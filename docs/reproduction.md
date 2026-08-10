# Reproducing the dissertation experiments

Run all commands from the repository root with Python 3.12.

## 1. Create the environment

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
```

## 2. Add and verify the data

Follow `docs/data_acquisition.md`. The configuration requires the exact SHA-256 of the dissertation CSV.

## 3. Smoke test

```bash
python -m gp_temperature_experiment run --config configs/smoke.yaml
```

This restricts evaluation to 2025, compares the Matérn-3/2 and periodic GPs, and uses reduced optimisation, posterior-draw, and bootstrap counts. It checks the complete path from CSV validation through saved metrics.

## 4. Confirmatory analysis

```bash
python -m gp_temperature_experiment run --config configs/confirmatory.yaml
```

The run fits the SE, Matérn-3/2, Matérn-5/2, periodic, locally periodic, and additive GP specifications plus the three dissertation baselines. Outputs are written to `outputs/confirmatory_v1/`.

The integrity-labelled rerun uses the same substantive settings but a separate output directory:

```bash
python -m gp_temperature_experiment run --config configs/confirmatory_integrity_v2.yaml
```

## 5. Sensitivity analyses

```bash
python -m gp_temperature_experiment run --config configs/sensitivity_alt_mean_v1.json
python -m gp_temperature_experiment run --config configs/sensitivity_utc_origin_v1.json
```

The first removes the smooth calendar-year component from the mean model. The second changes the civil-time origin to UTC. These are robustness probes, not additional confirmatory model searches.

## 6. Deterministic reproduction and statistical validation

To check exact reproducibility, run the confirmatory configuration twice into two different output roots. Make copies of the frozen configuration and change only `version_label` and `output_root`; do not overwrite prior output. Then run:

```bash
python -m gp_temperature_experiment.validation \
  --original outputs/reproducibility/original_v1 \
  --rerun outputs/reproducibility/rerun_v1 \
  --output outputs/validation_v1 \
  --repetitions 10000 \
  --seed 314159
```

This produces SHA-256 comparisons, paired year-block sign-flip tests with Benjamini--Hochberg correction, and year-block bootstrap intervals for coverage. The compact dissertation snapshot is in `results/validation/`.

## Expected runtime and storage

The smoke test is the appropriate installation check. The full confirmatory and sensitivity analyses perform many rolling-origin fits, multistart likelihood optimisations, and posterior simulations and therefore require substantially more time. Generated outputs are ignored by Git; preserve them in a separate immutable run directory if they are needed for audit.
