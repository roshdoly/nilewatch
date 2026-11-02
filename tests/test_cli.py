import numpy as np
import pandas as pd
import xarray as xr

from nilewatch.cli import main


def test_spi_and_map_end_to_end(tmp_path):
    rng = np.random.default_rng(7)
    time = pd.date_range("1991-01-01", "2024-12-01", freq="MS")
    lat, lon = np.linspace(9.0, 12.0, 4), np.linspace(36.0, 39.0, 5)
    rain = rng.gamma(2.0, 30.0, (len(time), len(lat), len(lon)))
    xr.Dataset({"precip": (("time", "lat", "lon"), rain)}, coords={"time": time, "lat": lat, "lon": lon}).to_netcdf(tmp_path / "p.nc")
    main(["spi", "--input", str(tmp_path / "p.nc"), "--scale", "3", "--out", str(tmp_path / "spi.nc")])
    out = xr.open_dataset(tmp_path / "spi.nc")
    assert "spi3" in out and np.isfinite(out["spi3"].isel(time=-1)).all()
    main(["map", "--input", str(tmp_path / "spi.nc"), "--date", "2024-08", "--out", str(tmp_path / "m.png")])
    assert (tmp_path / "m.png").stat().st_size > 1000
