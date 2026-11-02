# NileWatch

[![tests](https://github.com/roshdoly/nilewatch/actions/workflows/tests.yml/badge.svg)](https://github.com/roshdoly/nilewatch/actions/workflows/tests.yml)

Drought and water monitoring for Egypt and the Nile Basin, built on open satellite and climate data.

Egypt gets almost all of its water from the Nile, and the Nile's flow is set by rainfall over the Ethiopian Highlands and the Lake Victoria basin, thousands of kilometres upstream. NileWatch brings the signals that matter for that water supply into one place and keeps them current:

- **Rainfall and drought** over the whole basin, as standardized drought indices.
- **Groundwater** storage change in the Nubian and Nile Delta aquifers, from satellite gravity.
- **Reservoir and lake levels** (Lake Nasser, Lake Tana, Lake Victoria), from satellite altimetry.
- **Crop water stress** in the Nile Delta, from vegetation indices.

## Status

Early development. Working now:

- Download of CHIRPS v2.0 monthly rainfall (0.05°, 1981 to present) for predefined regions: Egypt, the Nile Basin, the Ethiopian Highlands, Lake Victoria and the Nile Delta.
- Standardized Precipitation Index (SPI) at any accumulation scale, vectorised over the grid, with careful handling of zero-rain months, which dominate most of Egypt.
- Maps of SPI fields with the WMO drought classes.
- Unit tests for the index and the data reader.

## Quick start

```bash
pip install -e ".[dev]"
pytest

# rainfall over the Ethiopian Highlands, 1991-2025
nilewatch download --region ethiopian-highlands --start 1991-01 --end 2025-12 --out data/chirps_highlands.nc

# 3-month SPI against the 1991-2020 climate
nilewatch spi --input data/chirps_highlands.nc --scale 3 --calib 1991 2020 --out data/spi3_highlands.nc

# map of one month
nilewatch map --input data/spi3_highlands.nc --date 2024-08 --out maps/spi3_highlands_2024-08.png
```

## Method notes

**SPI** (McKee et al., 1993). For each calendar month, a gamma distribution is fitted to the accumulated rainfall of that month over the calibration years (Thom's 1958 maximum-likelihood approximation), and each total is mapped to a standard normal deviate.

- **Zero rainfall.** Months with zero rainfall get the "centre of mass" probability recommended by Stagge et al. (2015). The common choice H(0) = q gives a *positive* SPI for a rainless month whenever most years are dry, which is wrong for desert climates.
- **Rarely wet months.** Calendar months that are wet in fewer than 30 % of calibration years have no meaningful SPI and are left empty rather than reported as noise.

**Data.**
- CHIRPS: Funk et al. (2015), *Scientific Data* 2, 150066.
- Africa monthly GeoTIFFs from the Climate Hazards Center, UC Santa Barbara.

## Roadmap

1. **SPEI.** Potential evapotranspiration from ERA5-Land (Penman-Monteith or Hargreaves), since in a hot climate rainfall alone misses evaporative drought.
2. **Groundwater.** GRACE / GRACE-FO mascon terrestrial water storage, with soil moisture from GLDAS removed, for the Nubian Sandstone and Nile Delta aquifers.
3. **Lake and reservoir levels.** Lake Nasser, Lake Tana and Lake Victoria from Hydroweb and DAHITI altimetry, set against the upstream rainfall indices.
4. **Nile Delta crops.** Sentinel-2 NDVI through public STAC catalogues, cloud masked, as seasonal anomalies.
5. **Automation.** Monthly scheduled updates, a small API (FastAPI), and a web dashboard with maps and time series per region.
6. **Alerts.** A monthly drought bulletin when a region crosses a drought class.

## License

MIT
