"""Great-circle distance calculations."""

import math

import pytest
from tabulate import tabulate


EARTH_RADIUS_KM = 6371.0
KM_TO_MILES = 0.621371

LOCATIONS = [
    ("New York", 40.7128, -74.0060),
    ("London", 51.5074, -0.1278),
    ("Tokyo", 35.6762, 139.6503),
    ("Sydney", -33.8688, 151.2093),
    ("Cape Town", -33.9249, 18.4241),
]


def normalize_longitude(longitude):
    """Return a longitude normalized into the inclusive range [-180, 180]."""
    return ((longitude + 180) % 360) - 180


def haversine(lat1, lon1, lat2, lon2):
    """Return the great-circle distance between two coordinates in kilometres."""
    if not -90 <= lat1 <= 90 or not -90 <= lat2 <= 90:
        raise ValueError("latitude must be between -90 and 90 degrees")

    lon1 = normalize_longitude(lon1)
    lon2 = normalize_longitude(lon2)

    lat1_radians = math.radians(lat1)
    lat2_radians = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    haversine_angle = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_radians)
        * math.cos(lat2_radians)
        * math.sin(delta_lon / 2) ** 2
    )
    central_angle = 2 * math.asin(math.sqrt(haversine_angle))
    return EARTH_RADIUS_KM * central_angle


def total_route_distance(locations=LOCATIONS):
    """Return the total great-circle distance through locations in order."""
    return sum(
        haversine(first[1], first[2], second[1], second[2])
        for first, second in zip(locations, locations[1:])
    )


def nearest_neighbor(location_name, locations=LOCATIONS):
    """Return the nearest other location and its distance in km and miles."""
    location = next(
        (location for location in locations if location[0] == location_name),
        None,
    )
    if location is None:
        raise ValueError(f"unknown location: {location_name}")

    _, latitude, longitude = location
    other_locations = [other for other in locations if other[0] != location_name]
    if not other_locations:
        raise ValueError("at least two locations are required")

    nearest_name, nearest_latitude, nearest_longitude = min(
        other_locations,
        key=lambda other: haversine(
            latitude,
            longitude,
            other[1],
            other[2],
        ),
    )
    distance_km = haversine(
        latitude,
        longitude,
        nearest_latitude,
        nearest_longitude,
    )
    return nearest_name, distance_km, distance_km * KM_TO_MILES


def print_distance_tables():
    """Print pairwise distances between all locations in kilometres and miles."""
    names = [name for name, _, _ in LOCATIONS]
    kilometer_rows = []
    mile_rows = []

    for name, latitude, longitude in LOCATIONS:
        kilometer_row = [name]
        mile_row = [name]
        for _, other_latitude, other_longitude in LOCATIONS:
            kilometers = haversine(
                latitude,
                longitude,
                other_latitude,
                other_longitude,
            )
            kilometer_row.append(kilometers)
            mile_row.append(kilometers * KM_TO_MILES)
        kilometer_rows.append(kilometer_row)
        mile_rows.append(mile_row)

    headers = ["Location", *names]
    print("Distances (km)")
    print(tabulate(kilometer_rows, headers=headers, floatfmt=".1f", tablefmt="grid"))
    print("\nDistances (miles)")
    print(tabulate(mile_rows, headers=headers, floatfmt=".1f", tablefmt="grid"))


def print_nearest_neighbors():
    """Print the closest location for each location in the list."""
    rows = []
    for name, _, _ in LOCATIONS:
        nearest_name, distance_km, distance_miles = nearest_neighbor(name)
        rows.append([name, nearest_name, distance_km, distance_miles])

    print("\nNearest neighbors")
    print(
        tabulate(
            rows,
            headers=["Location", "Closest location", "Distance (km)", "Distance (miles)"],
            floatfmt=".1f",
            tablefmt="grid",
        )
    )


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


if __name__ == "__main__":
    print_distance_tables()
    print_nearest_neighbors()
    route_distance_km = total_route_distance()
    print(
        f"\nTotal route distance: {route_distance_km:.1f} km "
        f"({route_distance_km * KM_TO_MILES:.1f} miles)"
    )
