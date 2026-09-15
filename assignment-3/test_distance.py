import pytest

from distance import haversine, normalize_longitude


def test_one_degree_of_longitude_at_equator():
    distance = haversine(0, 0, 0, 1)
    print(f"One degree of longitude at equator: {distance:.3f} km")

    assert distance == pytest.approx(111.195, abs=0.01)


def test_cleveland_to_akron_ohio():
    cleveland = (41.4993, -81.6944)
    akron = (41.0814, -81.5190)

    distance = haversine(*cleveland, *akron)
    print(f"Cleveland to Akron: {distance:.3f} km")

    assert distance == pytest.approx(48.724, abs=0.001)


@pytest.mark.parametrize("latitude", [-91, 91])
def test_latitude_outside_range_is_rejected(latitude):
    with pytest.raises(ValueError, match="latitude must be between -90 and 90 degrees"):
        haversine(latitude, 0, 0, 0)
    print(f"Latitude {latitude}: rejected")


def test_arbitrary_longitude_is_normalized():
    normalized = normalize_longitude(200)
    distance_from_200 = haversine(0, 200, 0, 0)
    distance_from_negative_160 = haversine(0, -160, 0, 0)
    print(f"Longitude 200 normalized to: {normalized}")
    print(f"Distance using 200: {distance_from_200:.3f} km")
    print(f"Distance using -160: {distance_from_negative_160:.3f} km")

    assert normalized == -160
    assert distance_from_200 == pytest.approx(distance_from_negative_160)
