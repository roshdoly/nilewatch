"""Maps of SPI fields."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import xarray as xr  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

BOUNDS = [-3.5, -2.0, -1.5, -1.0, 1.0, 1.5, 2.0, 3.5]
COLOURS = ["#7f0000", "#d7301f", "#fc8d59", "#f7f7f7", "#91bfdb", "#4575b4", "#08306b"]


def spi_map(field: xr.DataArray, title: str, out: Path) -> Path:
    """Save a map of one SPI field with the WMO classes as colour bands."""
    cmap = ListedColormap(COLOURS).with_extremes(bad="#d9d9d9")
    norm = BoundaryNorm(BOUNDS, cmap.N)
    fig, ax = plt.subplots(figsize=(7, 6))
    data = np.ma.masked_invalid(field.values)
    mesh = ax.pcolormesh(field["lon"], field["lat"], data, cmap=cmap, norm=norm, shading="auto")
    cb = fig.colorbar(mesh, ax=ax, ticks=BOUNDS[1:-1], shrink=0.85)
    cb.set_label("SPI (grey: no data or too dry for SPI)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    ax.set_aspect("equal")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out
