"""Standardized Precipitation Index (SPI) on gridded monthly precipitation.

The SPI (McKee et al., 1993) turns accumulated precipitation into a standard normal
deviate: for each calendar month, a gamma distribution is fitted to the accumulated
totals of that month over a calibration period, and each total is mapped through the
fitted cumulative distribution and the inverse standard normal.

Large parts of Egypt receive no rain in most months, so the handling of zeros matters:

* the probability of zero, q, is estimated from the calibration years;
* non-zero totals use H(x) = q + (1 - q) G(x), with G the fitted gamma CDF;
* zero totals use the "centre of mass" probability (n0 + 1) / (2 (n + 1)) recommended by
  Stagge et al. (2015), instead of H(0) = q, which gives positive SPI for a dry month
  whenever more than half of the years are dry;
* a calendar month whose calibration years are mostly dry (wet fraction below
  ``min_wet_fraction``) has no meaningful SPI and is returned as NaN.

The gamma parameters use Thom's (1958) maximum-likelihood approximation, which is
vectorised over the whole grid.

References
----------
McKee, T. B., Doesken, N. J., Kleist, J. (1993). The relationship of drought frequency
and duration to time scales. 8th Conference on Applied Climatology, 179-184.
Thom, H. C. S. (1958). A note on the gamma distribution. Monthly Weather Review 86, 117-122.
Stagge, J. H., Tallaksen, L. M., Gudmundsson, L., Van Loon, A. F., Stahl, K. (2015).
Candidate distributions for climatological drought indices (SPI and SPEI).
International Journal of Climatology 35, 4027-4040.
"""
from __future__ import annotations

import warnings

import numpy as np
from scipy import special, stats

# WMO (2012) SPI classes
WET_CLASSES = [(2.0, "extremely wet"), (1.5, "very wet"), (1.0, "moderately wet")]
DRY_CLASSES = [(-2.0, "extremely dry"), (-1.5, "severely dry"), (-1.0, "moderately dry")]


def accumulate(precip: np.ndarray, scale: int) -> np.ndarray:
    """Running sum over ``scale`` months along axis 0; the first ``scale - 1`` months are NaN."""
    if scale < 1:
        raise ValueError("scale must be at least 1")
    p = np.asarray(precip, dtype=float)
    out = np.full_like(p, np.nan)
    if p.shape[0] < scale:
        return out
    c = np.cumsum(np.concatenate([np.zeros((1,) + p.shape[1:]), p], axis=0), axis=0)
    out[scale - 1:] = c[scale:] - c[:-scale]
    return out


def gamma_thom(x: np.ndarray, axis: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Shape and scale of a gamma distribution by Thom's approximation, ignoring NaN and
    non-positive values. Where fewer than two positive values exist, both are NaN."""
    x = np.where(x > 0, x, np.nan)
    n = np.sum(np.isfinite(x), axis=axis)
    with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)          # all-NaN cells are handled below
        mean = np.nanmean(x, axis=axis)
        a = np.log(mean) - np.nanmean(np.log(x), axis=axis)
        shape = (1.0 + np.sqrt(1.0 + 4.0 * a / 3.0)) / (4.0 * a)
        scale = mean / shape
    bad = (n < 2) | ~np.isfinite(shape) | (a <= 0)
    shape = np.where(bad, np.nan, shape)
    scale = np.where(bad, np.nan, scale)
    return shape, scale


def spi(precip: np.ndarray, months: np.ndarray, years: np.ndarray, scale: int = 3,
        calibration: tuple[int, int] | None = None, min_wet_fraction: float = 0.3,
        min_years: int = 20) -> np.ndarray:
    """SPI of monthly precipitation.

    Parameters
    ----------
    precip : array (time, ...) of monthly totals in mm, NaN for missing.
    months, years : integer arrays (time,) giving each step's calendar month (1-12) and year.
    scale : accumulation period in months (1, 3, 6, 12 ...).
    calibration : first and last year used to fit the distributions; all years if None.
    min_wet_fraction : calendar months whose calibration totals are positive in fewer
        than this fraction of years get NaN.
    min_years : calendar months with fewer valid calibration years get NaN.

    Returns
    -------
    array shaped like ``precip`` with the SPI, NaN where undefined.
    """
    months = np.asarray(months)
    years = np.asarray(years)
    acc = accumulate(precip, scale)
    out = np.full(acc.shape, np.nan)
    if calibration is None:
        in_cal = np.ones(len(years), bool)
    else:
        in_cal = (years >= calibration[0]) & (years <= calibration[1])
    for m in range(1, 13):
        sel = months == m
        if not sel.any():
            continue
        cal = acc[sel & in_cal]
        n = np.sum(np.isfinite(cal), axis=0)
        n0 = np.sum(cal == 0, axis=0)
        with np.errstate(invalid="ignore", divide="ignore"):
            q = n0 / n
            p_zero = (n0 + 1.0) / (2.0 * (n + 1.0))
        shape, gscale = gamma_thom(cal, axis=0)
        x = acc[sel]
        with np.errstate(invalid="ignore", divide="ignore"):
            g = special.gammainc(shape, np.where(x > 0, x, 0.0) / gscale)
            h = np.where(x > 0, q + (1.0 - q) * g, p_zero)
        h = np.clip(h, 1e-6, 1.0 - 1e-6)
        z = stats.norm.ppf(h)
        ok = (n >= min_years) & ((1.0 - q) >= min_wet_fraction) & np.isfinite(shape)
        z = np.where(ok & np.isfinite(x), z, np.nan)
        out[sel] = z
    return out


def classify(value: float) -> str:
    """WMO (2012) class of one SPI value ('no data' for NaN)."""
    if not np.isfinite(value):
        return "no data"
    for bound, label in WET_CLASSES:
        if value >= bound:
            return label
    for bound, label in DRY_CLASSES:
        if value <= bound:
            return label
    return "near normal"
