import numpy as np
import rasterio
from rasterio.transform import from_origin

from nilewatch import chirps, regions


def test_month_url():
    assert chirps.month_url(2024, 3).endswith("/africa_monthly/tifs/chirps-v2.0.2024.03.tif.gz")


def test_read_region_clips_and_masks(tmp_path):
    # a 0.05 degree grid over 20-40 E, 20-35 N, like the CHIRPS Africa tiles
    res = 0.05
    nx, ny = int(20 / res), int(15 / res)
    data = np.arange(nx * ny, dtype="float32").reshape(ny, nx) % 200
    data[0, :] = chirps.NODATA
    tif = tmp_path / "test.tif"
    with rasterio.open(tif, "w", driver="GTiff", width=nx, height=ny, count=1, dtype="float32",
                       crs="EPSG:4326", transform=from_origin(20.0, 35.0, res, res), nodata=chirps.NODATA) as dst:
        dst.write(data, 1)
    da = chirps.read_region(tif, regions.bbox("nile-delta"))
    west, south, east, north = regions.bbox("nile-delta")
    assert float(da.lon.min()) >= west - res and float(da.lon.max()) <= east + res
    assert float(da.lat.min()) >= south - res and float(da.lat.max()) <= north + res
    assert np.isfinite(da.values).all()
    assert da.attrs["units"] == "mm/month"
