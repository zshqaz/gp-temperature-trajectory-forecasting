# Gaussian-process forecasting of London July temperatures

This repository contains the source code for a UK MSc dissertation on how covariance-kernel specification affects the predictive accuracy and uncertainty calibration of Gaussian-process models that forecast the remaining London July temperature trajectory after observations through 09:00 local time.

The analysis uses hourly ERA5-Land 2 m temperature at latitude 51.5, longitude 0.0. July days from 1940--2025 are represented as replicated 24-hour curves. Evaluation is rolling-origin by year for 2001--2025. The main probabilistic target is the temperature trajectory from 10:00--23:00; the daily post-09:00 maximum is a secondary derived target.

## Source-only repository policy

The repository contains no fitted parameters, score tables, predictions, generated figures, logs, dissertation results, or raw Copernicus data. Generated artifacts are written under `outputs/` and excluded by `.gitignore`.

Everything needed to regenerate the analysis is included except the separately distributed ERA5-Land CSV:

- data validation and curve-construction code;
- mean, covariance, optimisation, conditioning and baseline implementations;
- probabilistic scoring and uncertainty-calibration code;
- rolling-origin orchestration and deterministic validation routines;
- frozen primary, smoke-test and sensitivity configurations;
- unit tests and GitHub Actions configuration;
- documentation of the data source, design, modules, configuration and commands.

## Repository map

| Path | Purpose |
|---|---|
| `gp_temperature_experiment/` | Complete Python implementation |
| `configs/` | Frozen experiment configurations |
| `tests/` | Deterministic unit tests |
| `docs/data_acquisition.md` | Dataset retrieval, accepted schema and structural checks |
| `docs/experiment_design.md` | Statistical design and model comparison protocol |
| `docs/code_walkthrough.md` | Module-by-module implementation explanation |
| `docs/configuration_reference.md` | Configuration reference |
| `docs/reproduction.md` | Installation, execution and validation commands |

Downloaded ERA5 CSV files can be passed directly with `--data`; acceptance depends on their parsed columns, coordinate, timestamps, temperatures and complete-day structure rather than filename or serialization. 

## Citation and licensing

Use `CITATION.cff` and record the exact Git commit used for the analysis. The canonical repository is <https://github.com/zshqaz/gp-temperature-trajectory-forecasting>.

No software licence has yet been granted. Public visibility permits inspection and reproducibility review but does not by itself grant reuse rights. The author can add an open-source licence after checking university and data obligations.
