import geopandas as gpd
import dask_geopandas as dgpd
import pytest
from shapely.geometry import box

from src.utils import admin_stats, confidence_summary, join_to_admin, verify_area


def test_verify_area_matches_metric_area():
	fields = gpd.GeoDataFrame(
		{"metrics:area": [1_000_000.0]},
		geometry=[box(2.0, 45.0, 2.01, 45.01)],
		crs="EPSG:4326",
	)
	fields["metrics:area"] = fields.to_crs(fields.estimate_utm_crs()).geometry.area
	ddf = dgpd.from_geopandas(fields, npartitions=1)

	comparison = verify_area(ddf, n=1)

	assert comparison["computed_area"].iloc[0] == pytest.approx(
		comparison["metrics:area"].iloc[0], rel=1e-6
	)


def test_confidence_fraction_decreases_with_threshold():
	fields = gpd.GeoDataFrame(
		{"confidence": [10, 40, 60, 90]},
		geometry=[box(0, 0, 1, 1)] * 4,
		crs="EPSG:4326",
	)
	ddf = dgpd.from_geopandas(fields, npartitions=2)

	low_threshold = confidence_summary(ddf, threshold=25)
	high_threshold = confidence_summary(ddf, threshold=75)

	assert low_threshold["fraction_above_threshold"] == 0.75
	assert high_threshold["fraction_above_threshold"] == 0.25
	assert (
		low_threshold["fraction_above_threshold"]
		> high_threshold["fraction_above_threshold"]
	)


def test_joined_field_counts_sum_to_joined_fields():
	fields = gpd.GeoDataFrame(
		{
			"confidence": [70, 80, 90],
			"metrics:area": [100.0, 200.0, 300.0],
		},
		geometry=[
			box(0.1, 0.1, 0.2, 0.2),
			box(0.3, 0.3, 0.4, 0.4),
			box(1.1, 0.1, 1.2, 0.2),
		],
		crs="EPSG:4326",
	)
	admins = gpd.GeoDataFrame(
		{"GID_2": ["unit-a", "unit-b"]},
		geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)],
		crs="EPSG:4326",
	)
	joined = join_to_admin(
		dgpd.from_geopandas(fields, npartitions=2), admins
	)

	joined_count = len(joined.compute())
	counts = admin_stats(joined)["field_count"].compute()

	assert counts.sum() == joined_count == len(fields)
