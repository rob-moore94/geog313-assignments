from math import radians, sin, cos, asin, sqrt
from turtle import distance

def haversine(lat1, lon1, lat2, lon2):
    # convert degrees to radians, apply the haversine formula
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    # differences between latitudes and longitudes
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    # apply the haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    # and return the distance in kilometers (R = 6371 km)
    R = 6371
    distance = R * c
    return distance

if __name__ == "__main__":
    d = haversine(42.2506, -71.8231, 40.7128, -74.0060)
    print(f"Distance: {d:.2f} km")