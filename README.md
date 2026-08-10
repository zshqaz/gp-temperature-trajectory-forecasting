# Gaussian-process forecasting of London July temperatures

This repository is the reproducibility package for Songhai Zhang's UK MSc dissertation, supervised by Christian Offen. It studies how covariance-kernel specification affects the predictive accuracy and uncertainty calibration of Gaussian-process models that forecast the remaining London July temperature trajectory after observations through 09:00 local time.

The analysis uses hourly ERA5-Land 2 m temperature at latitude 51.5, longitude 0.0. July days from 1940--2025 are represented as replicated 24-hour curves. Evaluation is rolling-origin by year for 2001--2025. The main probabilistic target is the temperature trajectory from 10:00--23:00; the daily post-09:00 maximum is a secondary derived target.

## What is included

- `gp_temperature_experiment/`: data checks, mean model, covariance kernels, optimisation, posterior prediction, scoring, and validation code.
- `configs/`: frozen confirmatory, integrity, smoke-test, and sensitivity configurations.
- `tests/`: deterministic unit tests.
- `results/`: compact result tables, optimisation diagnostics, provenance, and the deterministic reproducibility comparison used in the dissertation.
- `docs/`: data acquisition, complete reproduction commands, experiment protocol, and validation notes.

The raw ERA5-Land file and large generated day- and horizon-level output tables are not committed. The analysed CSV is identified by SHA-256, and the program refuses to run if the checksum differs.

## Quick start

Python 3.12 is required. From the repository root:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements-lock.txt
python -m unittest discover -s tests -v
```

Place the downloaded ERA5-Land CSV at:

```text
data/reanalysis-era5-single-levels-timeseries-sfcb7pyzsqo.csv
```

Its required SHA-256 is:

```text
159bdc3a41b80e161c3190a56601bfaa414f4c2137289193e8fc506626cc4441
```

Run the short end-to-end check:

```bash
python -m gp_temperature_experiment run --config configs/smoke.yaml
```

Run the frozen confirmatory analysis:

```bash
python -m gp_temperature_experiment run --config configs/confirmatory.yaml
```

See [docs/reproduction.md](docs/reproduction.md) for the full analysis and validation sequence.

## Archived result snapshot

The included snapshot reports that the functional baseline obtained the lowest mean NLPD (1.772) and CRPS (0.828), while the best GP by those two scores was the additive GP (NLPD 1.928; CRPS 0.966). The pure periodic GP was notably under-covered (80% simultaneous coverage 0.535; 95% coverage 0.710). These values are reported here to make the repository auditable, not as a substitute for the dissertation's interpretation and limitations.

## Citation

Use the metadata in `CITATION.cff` and cite release `v1.0.0` when referring to the dissertation code. The canonical repository is:

<https://github.com/clqqqaz/gp-temperature-trajectory-forecasting>

## Data and licensing

ERA5-Land is obtained separately from the [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries). This repository does not redistribute Copernicus data.

No software licence has yet been granted. Public visibility permits inspection and reproducibility review but does not by itself grant reuse rights. The author can add an open-source licence later after checking university and data obligations.
