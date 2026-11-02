"""Bounding boxes (west, south, east, north) in degrees."""

REGIONS = {
    "egypt": (24.7, 21.7, 37.1, 31.7),
    "nile-basin": (21.8, -4.0, 41.0, 31.7),
    "ethiopian-highlands": (34.0, 6.0, 41.0, 14.5),
    "lake-victoria": (31.5, -3.1, 34.9, 0.6),
    "nile-delta": (29.5, 30.0, 32.4, 31.6),
}


def bbox(name: str) -> tuple[float, float, float, float]:
    try:
        return REGIONS[name]
    except KeyError:
        raise ValueError(f"unknown region {name!r}; choose from {', '.join(sorted(REGIONS))}") from None
