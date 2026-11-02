import numpy as np
import pytest

from nilewatch.spi import accumulate, classify, gamma_thom, spi


def monthly_axes(n_years, first=1981):
    years = np.repeat(np.arange(first, first + n_years), 12)
    months = np.tile(np.arange(1, 13), n_years)
    return years, months


def test_accumulate_sums_and_leading_nans():
    p = np.arange(1.0, 7.0)
    acc = accumulate(p, 3)
    assert np.isnan(acc[:2]).all()
    np.testing.assert_allclose(acc[2:], [6.0, 9.0, 12.0, 15.0])


def test_accumulate_scale_one_is_identity():
    p = np.random.default_rng(0).gamma(2.0, 10.0, (24, 3, 4))
    np.testing.assert_allclose(accumulate(p, 1), p)


def test_gamma_thom_recovers_parameters():
    x = np.random.default_rng(1).gamma(2.5, 20.0, 20000)
    shape, scale = gamma_thom(x)
    assert abs(shape - 2.5) < 0.1
    assert abs(scale - 20.0) < 1.0


def test_spi_is_standard_normal_for_gamma_rain():
    rng = np.random.default_rng(2)
    years, months = monthly_axes(60)
    rain = rng.gamma(2.0, 15.0, (len(years), 2, 2))
    z = spi(rain, months, years, scale=1)
    for m in range(1, 13):
        v = z[months == m].ravel()
        assert abs(v.mean()) < 0.2
        assert abs(v.std() - 1.0) < 0.2


def test_spi_increases_with_rain_within_a_month():
    rng = np.random.default_rng(3)
    years, months = monthly_axes(40)
    rain = rng.gamma(2.0, 15.0, len(years))
    z = spi(rain, months, years, scale=1)
    jan = months == 1
    order = np.argsort(rain[jan])
    assert np.all(np.diff(z[jan][order]) > 0)


def test_dry_months_give_nan_and_wet_months_are_finite():
    rng = np.random.default_rng(4)
    years, months = monthly_axes(40)
    rain = rng.gamma(2.0, 15.0, len(years))
    rain[months == 7] = 0.0                      # a rainless calendar month
    z = spi(rain, months, years, scale=1)
    assert np.isnan(z[months == 7]).all()
    assert np.isfinite(z[months == 1]).all()


def test_zero_rain_gets_negative_spi_when_dry_years_are_common():
    rng = np.random.default_rng(5)
    years, months = monthly_axes(50)
    rain = rng.gamma(2.0, 15.0, len(years))
    dry = rng.random(len(years)) < 0.6          # 60 % of years dry: H(0) = q would give SPI > 0
    rain[dry] = 0.0
    z = spi(rain, months, years, scale=1, min_wet_fraction=0.3)
    assert np.all(z[dry & np.isfinite(z)] < 0.0)


def test_calibration_period_is_respected():
    rng = np.random.default_rng(6)
    years, months = monthly_axes(60)
    rain = rng.gamma(2.0, 15.0, len(years))
    rain[years >= 2011] *= 0.3                    # a drier recent climate
    z = spi(rain, months, years, scale=1, calibration=(1981, 2010))
    assert np.nanmean(z[years >= 2011]) < -1.0
    assert abs(np.nanmean(z[years <= 2010])) < 0.2


@pytest.mark.parametrize("value,label", [
    (2.3, "extremely wet"), (1.6, "very wet"), (1.0, "moderately wet"), (0.0, "near normal"),
    (-1.0, "moderately dry"), (-1.7, "severely dry"), (-2.0, "extremely dry"), (float("nan"), "no data"),
])
def test_classify(value, label):
    assert classify(value) == label
