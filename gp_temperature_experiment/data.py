from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CurveData:
    curves: pd.DataFrame
    audit: dict[str, object]


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_july_curves(config: dict) -> CurveData:
    path = Path(config["data_path"])
    analysis = config["analysis"]
    actual_hash = sha256_file(path)
    if actual_hash.lower() != config["expected_sha256"].lower():
        raise ValueError(
            f"SHA-256 mismatch: expected {config['expected_sha256']}, got {actual_hash}"
        )

    raw = pd.read_csv(
        path,
        usecols=["valid_time", "t2m", "latitude", "longitude"],
        dtype={"t2m": "float64", "latitude": "float64", "longitude": "float64"},
    )
    source_rows = int(len(raw))
    raw["valid_time"] = pd.to_datetime(raw["valid_time"], utc=True, errors="raise")

    duplicate_count = int(raw["valid_time"].duplicated().sum())
    missing_t2m = int(raw["t2m"].isna().sum())
    coords = raw[["latitude", "longitude"]].drop_duplicates()
    if duplicate_count:
        raise ValueError(f"Duplicate UTC timestamps found: {duplicate_count}")
    if missing_t2m:
        raise ValueError(f"Missing t2m values found: {missing_t2m}")
    if len(coords) != 1:
        raise ValueError(f"Expected one grid point, found {len(coords)}")
    latitude = float(coords.iloc[0]["latitude"])
    longitude = float(coords.iloc[0]["longitude"])
    if not np.isclose(latitude, 51.5) or not np.isclose(longitude, 0.0):
        raise ValueError(f"Unexpected coordinate: ({latitude}, {longitude})")

    # The prospective rule excludes 2026 before summaries or fitted preprocessing.
    raw = raw.loc[raw["valid_time"].dt.year <= analysis["last_year"]].copy()
    local = raw["valid_time"].dt.tz_convert(analysis["timezone"])
    raw["local_time"] = local
    raw["local_year"] = local.dt.year
    raw["local_month"] = local.dt.month
    raw["local_hour"] = local.dt.hour
    raw["local_date"] = local.dt.date
    raw["temperature_c"] = raw["t2m"] - 273.15

    mask = (
        raw["local_year"].between(analysis["first_year"], analysis["last_year"])
        & raw["local_month"].eq(analysis["month"])
    )
    july = raw.loc[mask, ["local_date", "local_year", "local_hour", "temperature_c"]]
    local_cell_counts = july.groupby(["local_date", "local_hour"], sort=True).size()
    duplicate_local_cells = local_cell_counts.loc[local_cell_counts > 1]
    if analysis["local_duplicate_hour_policy"] != "mean":
        raise ValueError("Only the prospectively recorded local duplicate policy 'mean' is supported.")
    # Britain moved from double summer time to summer time on 1945-07-15,
    # repeating local 02:00. Collapse any repeated civil-hour cell by its mean
    # so every replicated curve retains the common 24-hour grid.
    july = (
        july.groupby(["local_date", "local_year", "local_hour"], as_index=False, sort=True)[
            "temperature_c"
        ]
        .mean()
    )
    counts = july.groupby("local_date", sort=True)["local_hour"].agg(["count", "nunique"])
    bad = counts.loc[(counts["count"] != 24) | (counts["nunique"] != 24)]
    if not bad.empty:
        raise ValueError(f"Incomplete or duplicated local July days: {bad.index.tolist()[:10]}")

    curves = july.pivot(index="local_date", columns="local_hour", values="temperature_c")
    curves = curves.reindex(columns=list(range(24))).sort_index()
    if curves.isna().any().any():
        raise ValueError("Missing values remain after constructing 24-hour curves.")
    years = pd.Index([d.year for d in curves.index], dtype="int64")
    curves.insert(0, "year", years.to_numpy())
    curves.index = pd.Index([d.isoformat() for d in curves.index], name="date")

    expected_days = (
        (analysis["last_year"] - analysis["first_year"] + 1) * 31
    )
    if analysis["month"] == 7 and len(curves) != expected_days:
        raise ValueError(f"Expected {expected_days} complete July days, found {len(curves)}")

    audit = {
        "path": str(path.resolve()),
        "sha256": actual_hash,
        "source_rows": source_rows,
        "analysis_scope_rows": int(len(raw)),
        "analysis_days": int(len(curves)),
        "analysis_hourly_rows": int(len(curves) * 24),
        "first_year": int(curves["year"].min()),
        "last_year": int(curves["year"].max()),
        "latitude": latitude,
        "longitude": longitude,
        "duplicate_timestamps": duplicate_count,
        "missing_t2m": missing_t2m,
        "temperature_c_min": float(curves[list(range(24))].to_numpy().min()),
        "temperature_c_max": float(curves[list(range(24))].to_numpy().max()),
        "timezone": analysis["timezone"],
        "local_duplicate_hour_groups": int(len(duplicate_local_cells)),
        "local_duplicate_hour_policy": analysis["local_duplicate_hour_policy"],
        "local_duplicate_cells": [
            {"date": date.isoformat(), "hour": int(hour), "source_rows": int(count)}
            for (date, hour), count in duplicate_local_cells.items()
        ],
        "status": "passed",
    }
    return CurveData(curves=curves, audit=audit)
