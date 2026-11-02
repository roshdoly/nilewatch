"""Download CHIRPS v2.0 monthly rainfall for a region and stack it into one dataset.

CHIRPS (Climate Hazards Group InfraRed Precipitation with Station data; Funk et al., 2015,
Scientific Data 2, 150066) is a 0.05 degree, quasi-global rainfall record from 1981 on.
The Africa monthly GeoTIFFs are used here because they cover Egypt and the Nile Basin and
are small (one gzipped file per month).
"""
from __future__ import annotations

import gzip
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
import xarray as xr
from rasterio.windows import from_bounds

BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs"
NODATA = -9999.0


def month_url(year: int, month: int) -> str:
    return f"{BASE_URL}/chirps-v2.0.{year}.{month:02d}.tif.gz"


def fetch_month(year: int, month: int, cache: Path, session: requests.Session | None = None) -> Path:
    """The GeoTIFF of one month, downloaded and unzipped into ``cache`` if not already there."""
    cache.mkdir(parents=True, exist_ok=True)
    tif = cache / f"chirps-v2.0.{year}.{month:02d}.tif"
    if tif.exists():
        return tif
    http = session or requests.Session()
    gz = tif.with_suffix(".tif.gz")
    with http.get(month_url(year, month), stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(gz, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    with gzip.open(gz, "rb") as src, open(tif, "wb") as dst:
        shutil.copyfileobj(src, dst)
    gz.unlink()
    return tif


def read_region(tif: Path, bbox: tuple[float, float, float, float]) -> xr.DataArray:
    """Precipitation (mm) inside ``bbox`` = (west, south, east, north), NaN where no data."""
    west, south, east, north = bbox
    with rasterio.open(tif) as src:
        window = from_bounds(west, south, east, north, transform=src.transform).round_offsets().round_lengths()
        data = src.read(1, window=window).astype(float)
        transform = src.window_transform(window)
        nodata = src.nodata if src.nodata is not None else NODATA
    data[data == nodata] = np.nan
    data[data < 0] = np.nan
    ny, nx = data.shape
    lon = transform.c + transform.a * (np.arange(nx) + 0.5)
    lat = transform.f + transform.e * (np.arange(ny) + 0.5)
    return xr.DataArray(data, coords={"lat": lat, "lon": lon}, dims=("lat", "lon"), name="precip",
                        attrs={"units": "mm/month", "source": "CHIRPS v2.0"})


def download(bbox: tuple[float, float, float, float], start: str, end: str, cache: Path,
             keep_tifs: bool = True) -> xr.Dataset:
    """Monthly precipitation from ``start`` to ``end`` (inclusive, 'YYYY-MM') inside ``bbox``."""
    months = pd.period_range(start, end, freq="M")
    session = requests.Session()
    layers = []
    for p in months:
        tif = fetch_month(p.year, p.month, cache, session)
        layers.append(read_region(tif, bbox))
        if not keep_tifs:
            tif.unlink()
    da = xr.concat(layers, dim=pd.Index(months.to_timestamp(), name="time"))
    return da.to_dataset()
