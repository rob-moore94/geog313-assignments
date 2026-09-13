"""Great-circle distance calculations."""

import math


EARTH_RADIUS_KM = 6371.0

LOCATIONS = [
    ("New York", 40.7128, -74.0060),
    ("London", 51.5074, -0.1278),
    ("Tokyo", 35.6762, 139.6503),
    ("Sydney", -33.8688, 151.2093),
    ("Cape Town", -33.9249, 18.4241),
]


def haversine(lat1, lon1, lat2, lon2):
    """Return the great-circle distance between two coordinates in kilometres."""
    if not -90 <= lat1 <= 90 or not -90 <= lat2 <= 90:
        raise ValueError("latitude must be between -90 and 90 degrees")

    lon1 = ((lon1 + 180) % 360) - 180
    lon2 = ((lon2 + 180) % 360) - 180

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
