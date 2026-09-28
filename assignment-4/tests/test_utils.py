import numpy as np
import xarray as xr

from src.utils import (
    anomalies,
    area_weighted_mean,
    coarsen_to_4deg,
    composite,
    detect_events,
    interp_to_4deg,
    linear_trend,
    monthly_climatology,
    rolling_index,
    subset_region,
)


def test_area_weighted_mean_constant_field_returns_constant() -> None:
    field = xr.DataArray(
        np.full((2, 3), 4.5),
        coords={"lat": [-30, 30], "lon": [0, 2, 4]},
        dims=("lat", "lon"),
    )

    result = area_weighted_mean(field)

    assert result.item() == 4.5


def test_anomalies_have_zero_baseline_monthly_mean() -> None:
    time = np.arange("2000-01", "2002-01", dtype="datetime64[M]")
    values = xr.DataArray(
        np.arange(24, dtype=float),
        coords={"time": time},
        dims="time",
    )

    climatology = monthly_climatology(values, baseline=("2000", "2001"))
    result = anomalies(values, climatology)

    assert np.allclose(result.groupby("time.month").mean(), 0.0)


def test_coarsen_to_4deg_returns_expected_shape_and_values() -> None:
    field = xr.DataArray(
        np.arange(16, dtype=float).reshape(4, 4),
        coords={"lat": [0, 2, 4, 6], "lon": [10, 12, 14, 16]},
        dims=("lat", "lon"),
    )

    result = coarsen_to_4deg(field)

    assert result.shape == (2, 2)
    assert np.allclose(result, [[2.5, 4.5], [10.5, 12.5]])


def test_interp_to_4deg_uses_every_second_coordinate() -> None:
    field = xr.DataArray(
        np.arange(16, dtype=float).reshape(4, 4),
        coords={"lat": [0, 2, 4, 6], "lon": [10, 12, 14, 16]},
        dims=("lat", "lon"),
    )

    result = interp_to_4deg(field)

    assert result.shape == (2, 2)
    assert np.array_equal(result.lat, [0, 4])
    assert np.array_equal(result.lon, [10, 14])
    assert np.allclose(result, [[0, 2], [8, 10]])


def test_rolling_index_is_centered() -> None:
    index = xr.DataArray([1.0, 2.0, 3.0, 4.0, 5.0], dims="time")

    result = rolling_index(index)

    assert np.allclose(result, [np.nan, 2.0, 3.0, 4.0, np.nan], equal_nan=True)


def test_detect_events_finds_warm_and_cold_runs() -> None:
    time = np.arange("2000-01", "2000-08", dtype="datetime64[M]")
    index = xr.DataArray(
        [0.6, 0.8, 0.7, 0.0, -0.6, -0.9, -0.7],
        coords={"time": time},
        dims="time",
    )

    result = detect_events(index)

    assert result["warm"] == [
        {"start": time[0], "end": time[2], "peak": 0.8}
    ]
    assert result["cold"] == [
        {"start": time[4], "end": time[6], "peak": -0.9}
    ]


def test_composite_averages_selected_event_months() -> None:
    time = np.arange("2000-01", "2000-04", dtype="datetime64[M]")
    field = xr.DataArray(
        np.arange(12, dtype=float).reshape(3, 2, 2),
        coords={"time": time, "lat": [0, 2], "lon": [10, 12]},
        dims=("time", "lat", "lon"),
    )

    result = composite(field, time[[0, 2]])

    assert result.dims == ("lat", "lon")
    assert np.allclose(result, [[4.0, 5.0], [6.0, 7.0]])


def test_linear_trend_returns_degrees_per_decade() -> None:
    time = np.arange("2000-01", "2005-01", dtype="datetime64[M]")
    years = np.arange(time.size, dtype=float) / 12
    field = xr.DataArray(
        np.column_stack((0.1 * years, -0.2 * years)).reshape(time.size, 1, 2),
        coords={"time": time, "lat": [0], "lon": [10, 12]},
        dims=("time", "lat", "lon"),
    )

    result = linear_trend(field)

    assert result.dims == ("lat", "lon")
    assert np.allclose(result, [[1.0, -2.0]])


def test_subset_region_handles_descending_latitudes() -> None:
    field = xr.DataArray(
        np.zeros((5, 2)),
        coords={"lat": [10, 5, 0, -5, -10], "lon": [0, 10]},
        dims=("lat", "lon"),
    )

    result = subset_region(field, lat_bounds=(-5, 5), lon_bounds=(0, 10))

    assert np.array_equal(result.lat, [5, 0, -5])
