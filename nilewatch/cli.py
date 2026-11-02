"""Command line: nilewatch download | spi | map."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr

from . import chirps, plot, regions
from .spi import spi


def cmd_download(a: argparse.Namespace) -> None:
    ds = chirps.download(regions.bbox(a.region), a.start, a.end, Path(a.cache), keep_tifs=not a.no_cache)
    ds.attrs["region"] = a.region
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(a.out)
    print(f"wrote {a.out}: {ds.sizes['time']} months, {ds.sizes['lat']} x {ds.sizes['lon']} cells")


def cmd_spi(a: argparse.Namespace) -> None:
    ds = xr.open_dataset(a.input)
    t = ds["time"].dt
    values = spi(ds["precip"].values, t.month.values, t.year.values, scale=a.scale,
                 calibration=(a.calib[0], a.calib[1]), min_wet_fraction=a.min_wet)
    out = xr.Dataset({f"spi{a.scale}": (ds["precip"].dims, values)}, coords=ds.coords)
    out[f"spi{a.scale}"].attrs.update(long_name=f"SPI-{a.scale}", calibration=f"{a.calib[0]}-{a.calib[1]}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_netcdf(a.out)
    share = np.isfinite(values[-1]).mean()
    print(f"wrote {a.out}; {share:.0%} of cells have an SPI in the last month")


def cmd_map(a: argparse.Namespace) -> None:
    ds = xr.open_dataset(a.input)
    name = next(iter(ds.data_vars))
    field = ds[name].sel(time=a.date)
    if "time" in field.dims:
        field = field.isel(time=0)
    out = plot.spi_map(field, f"{ds[name].attrs.get('long_name', name)}, {a.date}", Path(a.out))
    print(f"wrote {out}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="nilewatch", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download", help="CHIRPS monthly rainfall for a region")
    d.add_argument("--region", default="egypt", choices=sorted(regions.REGIONS))
    d.add_argument("--start", default="1991-01")
    d.add_argument("--end", required=True, help="last month, YYYY-MM")
    d.add_argument("--cache", default="data/cache")
    d.add_argument("--no-cache", action="store_true", help="delete each GeoTIFF after reading it")
    d.add_argument("--out", required=True)
    d.set_defaults(func=cmd_download)
    s = sub.add_parser("spi", help="SPI from a precipitation file")
    s.add_argument("--input", required=True)
    s.add_argument("--scale", type=int, default=3)
    s.add_argument("--calib", type=int, nargs=2, default=[1991, 2020], metavar=("FIRST", "LAST"))
    s.add_argument("--min-wet", type=float, default=0.3, help="minimum wet fraction for a defined SPI")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_spi)
    m = sub.add_parser("map", help="map one month of an SPI file")
    m.add_argument("--input", required=True)
    m.add_argument("--date", required=True, help="YYYY-MM")
    m.add_argument("--out", required=True)
    m.set_defaults(func=cmd_map)
    a = ap.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
