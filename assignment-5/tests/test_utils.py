import numpy as np
import xarray as xr
from shapely.geometry import Point

from src.utils import ndvi, reproject_geometry, shift_to360, utm_epsg


def test_utm_epsg_returns_southern_hemisphere_zones():
	assert utm_epsg(179.9, -1) == (60, "south", 32760)
	assert utm_epsg(-179.9, -1) == (1, "south", 32701)


def test_reproject_geometry_round_trips_point():
	original = Point(179.9, -16.8)
	projected = reproject_geometry(original, "EPSG:4326", "EPSG:32760")
	round_tripped = reproject_geometry(projected, "EPSG:32760", "EPSG:4326")

	assert round_tripped.distance(original) < 1e-9


def test_shift_to360_rewrites_negative_longitude():
	shifted = shift_to360(Point(-178.3, -16.1))

	assert shifted.x == 181.7
	assert shifted.y == -16.1


def test_ndvi_is_bounded_and_handles_zero_denominator():
	red = xr.DataArray([1, 2, 0], dims="x")
	nir = xr.DataArray([3, 0, 0], dims="x")

	result = ndvi(red, nir)

	assert np.allclose(result.values[:2], [0.5, -1.0])
	assert np.isnan(result.values[2])
	assert float(result.min(skipna=True)) >= -1
	assert float(result.max(skipna=True)) <= 1
