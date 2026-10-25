from datetime import datetime

import dask.dataframe as dd
import numpy as np
import pandas as pd
import pytest
import xarray as xr
from pystac import Item

from src.utils import (
    dedupe_items,
    daily_values,
    mask_clouds,
    monthly_totals,
    ndwi,
    stations_within,
    to_reflectance,
    water_area,
)


def _band_data(values, bands=("green", "nir", "scl")):
    """Build a small scene stack with the coordinates used by the utilities."""
    return xr.DataArray(
        np.asarray(values, dtype=float),
        dims=("time", "band", "y", "x"),
        coords={
            "time": [pd.Timestamp("2023-01-01")],
            "band": list(bands),
            "y": [20, 0],
            "x": [0, 20],
        },
    )


def test_ndwi_known_values():
    stack = _band_data([[[[0.6, 0.2], [0.8, 0.4]], [[0.2, 0.6], [0.4, 0.8]], [[4, 4], [4, 4]]]])

    result = ndwi(stack)

    np.testing.assert_allclose(
        result.values,
        [[[(0.6 - 0.2) / 0.8, (0.2 - 0.6) / 0.8],
          [(0.8 - 0.4) / 1.2, (0.4 - 0.8) / 1.2]]],
    )


def test_mask_clouds_masks_class_9_and_keeps_class_4():
    stack = _band_data([[[[0.6, 0.6], [0.6, 0.6]],
                         [[0.2, 0.2], [0.2, 0.2]],
                         [[9, 4], [4, 9]]]])

    result = mask_clouds(stack)

    assert np.isnan(result.sel(band="green").values[0, 0, 0])
    assert result.sel(band="green").values[0, 0, 1] == 0.6


def test_water_area_counts_water_pixels_and_valid_fraction():
    ndwi_data = xr.DataArray(
        [[0.5, -0.1], [np.nan, 0.2]],
        dims=("y", "x"),
        coords={"y": [20, 0], "x": [0, 20]},
    )

    result = water_area(ndwi_data).compute()

    assert result["water_km2"].item() == pytest.approx(0.0008)
    assert result["valid_fraction"].item() == pytest.approx(0.75)


def _item(item_id, tile, baseline, date="2023-01-01"):
    item = Item(
        id=item_id,
        geometry={"type": "Point", "coordinates": [-121, 38]},
        bbox=[-121, 38, -121, 38],
        datetime=datetime.fromisoformat(date),
        properties={
            "s2:mgrs_tile": tile,
            "s2:processing_baseline": baseline,
        },
    )
    return item


def test_dedupe_items_filters_tile_and_keeps_highest_baseline():
    items = [
        _item("old", "10SFH", "03.00"),
        _item("new", "10SFH", "04.00"),
        _item("other-tile", "10SFG", "99.00"),
        _item("next-day", "10SFH", "03.00", "2023-01-02"),
    ]

    result = dedupe_items(items, "10SFH")

    assert {item.id for item in result} == {"new", "next-day"}


def test_to_reflectance_corrects_baseline_offset_and_preserves_scl():
    stack = xr.DataArray(
        np.array(
            [
                [[[1000]], [[1000]], [[4]]],
                [[[2000]], [[2000]], [[9]]],
            ],
            dtype=float,
        ),
        dims=("time", "band", "y", "x"),
        coords={
            "time": ["old", "new"],
            "band": ["green", "nir", "scl"],
            "y": [0],
            "x": [0],
            "s2:processing_baseline": ("time", ["03.00", "04.00"]),
        },
    )

    reflectance, scl = to_reflectance(stack)

    np.testing.assert_allclose(reflectance.sel(band="green").values, [[[0.1]], [[0.1]]])
    np.testing.assert_array_equal(scl.values, stack.sel(band="scl").values)


def test_stations_within_uses_geodesic_radius():
    stations = pd.DataFrame(
        {
            "station": ["near", "far"],
            "latitude": [0.0, 0.45],
            "longitude": [0.09, 0.0],
            "name": ["Near", "Far"],
        }
    )

    result = stations_within(stations, lon=0.0, lat=0.0, radius_km=30)

    assert result["station"].tolist() == ["near"]
    assert result["distance_km"].iloc[0] == pytest.approx(10, abs=0.2)


def test_monthly_totals_converts_units_and_masks_incomplete_month():
    dates = pd.date_range("2023-01-01", "2023-01-31", freq="D").tolist()
    dates += pd.date_range("2023-02-01", "2023-02-28", freq="D")[:10].tolist()
    # Start with GHCN tenths of mm and verify the conversion through daily_values.
    raw = pd.DataFrame(
        {
            "station": ["TEST"] * len(dates),
            "date": dates,
            "value": [10] * len(dates),
            "qflag": [None] * len(dates),
        }
    )
    daily = daily_values(dd.from_pandas(raw, npartitions=2), ["TEST"])

    result = monthly_totals(daily, min_fraction=0.9)

    assert result.loc["2023-01-01"] == pytest.approx(31.0)
    assert np.isnan(result.loc["2023-02-01"])