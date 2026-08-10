# ERA5-Land data acquisition

## Source

- Provider: Copernicus Climate Change Service Climate Data Store.
- Dataset: ERA5 hourly time-series data on single levels from 1940 to present (`reanalysis-era5-land-timeseries`).
- Variable used: 2 m temperature (`t2m`).
- Point: latitude 51.5, longitude 0.0.
- Temporal analysis scope: July 1940--2025. Any 2026 observations are prospectively excluded by the analysis configuration and code.
- Source page: <https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries>

Download the point time series through the CDS interface or API under the terms shown by CDS. Export or retain a CSV containing the columns `valid_time`, `t2m`, `latitude`, and `longitude`, then save it as:

```text
data/reanalysis-era5-single-levels-timeseries-sfcb7pyzsqo.csv
```

## Integrity check

The exact file analysed for the dissertation had:

```text
SHA-256: 159bdc3a41b80e161c3190a56601bfaa414f4c2137289193e8fc506626cc4441
Source rows: 758,736
Rows in the 1940--2025 analysis scope: 753,888
Coordinates: 51.5, 0.0
```

The loader checks the checksum, required columns, timestamps, missing temperatures, coordinates, July day completeness, and the expected 2,666 complete daily curves. Rows dated after 2025 are excluded before fitting or summary calculations. The checksum is intentionally frozen: a newly downloaded or differently serialised CSV must not silently be treated as the dissertation dataset.

On PowerShell, verify the file with:

```powershell
Get-FileHash -Algorithm SHA256 data\reanalysis-era5-single-levels-timeseries-sfcb7pyzsqo.csv
```

On Linux or macOS:

```bash
sha256sum data/reanalysis-era5-single-levels-timeseries-sfcb7pyzsqo.csv
```

The raw file is not included in this public repository because it remains a separately distributed Copernicus product.
