# Gaussian-process forecasting of London July temperatures

This is the source-code repository for Songhai Zhang's UK MSc dissertation, supervised by Christian Offen. It studies how covariance-kernel specification affects the predictive accuracy and uncertainty calibration of probabilistic forecasts for the rest of a London July day after temperatures have been observed through 09:00 local time.

The analysis treats each July day as a 24-hour curve. Its primary target is the joint temperature trajectory from 10:00 to 23:00; the post-09:00 daily maximum is a secondary functional of that trajectory. The data source is hourly ERA5-Land 2 m temperature at latitude 51.5, longitude 0.0, with expanding-window evaluation by held-out year.

## Source-only repository policy

This repository intentionally contains no fitted parameters, score tables, predictions, generated figures, logs, or dissertation results. Those artifacts are created locally under `outputs/` and are excluded by `.gitignore`. The raw Copernicus data are also excluded. This keeps the public project focused on auditable source code and prevents generated evidence from being mistaken for inputs.

Everything required to regenerate the analysis is included except the separately distributed ERA5-Land CSV:

- all data validation and curve-construction code;
- all mean, covariance, optimisation, conditioning and baseline implementations;
- all probabilistic scoring and uncertainty-calibration code;
- rolling-origin experiment orchestration and provenance recording;
- deterministic validation routines;
- frozen primary, smoke-test and sensitivity configurations;
- unit tests and GitHub Actions configuration;
- documentation explaining the design, source modules, configuration and commands.

## Repository map

| Path | Purpose |
|---|---|
| `gp_temperature_experiment/` | Complete Python implementation |
| `configs/` | Frozen JSON-compatible experiment configurations |
| `tests/` | Deterministic tests for kernels, conditioning, optimisation, scoring and validation |
| `data/README.md` | Required local data location |
| `docs/data_acquisition.md` | Dataset retrieval, schema and checksum checks |
| `docs/experiment_design.md` | Statistical design and model comparison protocol |
| `docs/code_walkthrough.md` | Module-by-module explanation and execution flow |
| `docs/configuration_reference.md` | Meaning of every configuration section |
| `docs/reproduction.md` | Installation, execution and validation commands |

## Quick start

Python 3.12 is required. From the repository root:

```bash
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install the pinned runtime dependencies and the local package, then run the tests:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
```

Download the data as described in [docs/data_acquisition.md](docs/data_acquisition.md) and save the CSV as:

```text
data/reanalysis-era5-single-levels-timeseries-sfcb7pyzsqo.csv
```

Run the reduced end-to-end check:

```bash
python -m gp_temperature_experiment run --config configs/smoke.yaml
```

Run the frozen primary experiment:

```bash
python -m gp_temperature_experiment run --config configs/confirmatory.yaml
```

Both commands write new artifacts beneath `outputs/`; they do not require or read any precomputed results. See [docs/reproduction.md](docs/reproduction.md) for the full primary, sensitivity and deterministic-validation sequence.

## Method implemented

For each held-out year, the program fits the mean function using earlier July days only, subtracts that mean, estimates each covariance kernel by multistart maximum likelihood, and conditions the fitted Gaussian process on hours 00:00--09:00. Posterior trajectory draws are evaluated using marginal NLPD and CRPS, joint energy and variogram scores, pointwise and simultaneous interval coverage, and the induced distribution of the daily maximum. Persistence, analogue and functional-ridge forecasts are fitted on the same training folds as comparison models.

The implementation and equations are explained in [docs/code_walkthrough.md](docs/code_walkthrough.md); the prospective comparison rules are documented in [docs/experiment_design.md](docs/experiment_design.md).

## Citation

Use `CITATION.cff` and cite the exact Git commit used to run the analysis. The canonical repository is <https://github.com/clqqqaz/gp-temperature-trajectory-forecasting>.

## Data and licensing

ERA5-Land is obtained separately from the [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries). This repository does not redistribute Copernicus data.

No software licence has yet been granted. Public visibility permits inspection and reproducibility review but does not by itself grant reuse rights. The author can add an open-source licence after checking university and data obligations.
