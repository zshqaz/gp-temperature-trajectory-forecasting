# ERA5-Land data acquisition

## Source

- Provider: Copernicus Climate Change Service Climate Data Store.
- Dataset: ERA5 hourly time-series data on single levels from 1940 to present (`reanalysis-era5-land-timeseries`).
- Variable used: 2 m temperature (`t2m`).
- Point: latitude 51.5, longitude 0.0.
- Temporal analysis scope: July 1940--2025. Any 2026 observations are prospectively excluded by the analysis configuration and code.
- Source page: <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries>

Download the point time series through the CDS interface or API under the terms shown by CDS. Export or retain a CSV containing the columns `valid_time`, `t2m`, `latitude`, and `longitude`. You may save it at the configuration's default path:

```text
data/reanalysis-era5-single-levels-timeseries-sfcb7pyzsqo.csv
```

Alternatively, keep the downloaded filename and provide it directly:

```bash
python -m gp_temperature_experiment run \
  --config configs/smoke.yaml \
  --data path/to/downloaded-era5.csv
```

The same `--data` option works with the primary and sensitivity configurations.

## Structural validation

The loader does not require a particular filename or byte-for-byte file representation. It validates the data after reading the CSV. The required content is:

```text
Columns: valid_time, t2m, latitude, longitude
Coordinate: latitude 51.5, longitude 0.0
Time values: parseable timestamps with no duplicated UTC timestamps
Temperature: non-missing t2m values in Kelvin
Coverage: complete hourly July days for the configured analysis years
```

The program checks the required columns, timestamp parsing, missing temperatures, coordinates, July day completeness, and the expected number of complete daily curves implied by the configured year range. Rows after the configured final year are excluded before fitting or summary calculations. A newly downloaded or differently serialised CSV is therefore accepted when its contents satisfy the same structural rules.

The raw file is not included in this public repository because it remains a separately distributed Copernicus product.
