from math import radians, sin, cos, asin, sqrt
from tabulate import tabulate
from geopy.distance import geodesic

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

# geodesic WGS84 distance
def calculate_distance(lat1, lon1, lat2, lon2):
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)

    distance = geodesic(point1, point2).kilometers

    return distance

if __name__ == "__main__":
    # more locations
    locations = [
        ("lakewood", 41.494092, -81.796620),
        ("chico", 39.73682, -121.82390),
        ("san francisco", 37.7749, -122.4194),
        ("costa rica", 9.78456,-84.57665),
        ("detroit", 42.34150,-83.07653)
    ]

    # Loop through all unique pairs of locations
    table = []

    for i in range(len(locations)):
        for j in range(i + 1, len(locations)):
            name1, lat1, lon1 = locations[i]
            name2, lat2, lon2 = locations[j]

            distance = haversine(lat1, lon1, lat2, lon2)

            table.append([name1, name2, distance])

    print(tabulate(
        table,
        headers=["Location 1", "Location 2", "Distance (km)"],
        floatfmt=".1f"
    ))
# Nearest neighbor function
def nearest_neighbor(target, locations):
    name1, lat1, lon1 = target
    nearest_name = None
    nearest_distance = float('inf')

    for name2, lat2, lon2 in locations:
        if name2 == name1:
            continue  # skip the same location
        distance = haversine(lat1, lon1, lat2, lon2)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_name = name2

    return nearest_name, nearest_distance
# produce output table for nearest neighbor
nearest_table = []

# miles and kilometers table
for location in locations:
    nearest_name, nearest_distance = nearest_neighbor(location, locations)

    nearest_miles = nearest_distance * 0.621371 #conversion factor from km to miles

    nearest_table.append([
        location[0],
        nearest_name,
        nearest_distance,
        nearest_miles
    ])
# print table
print(tabulate(
    nearest_table,
    headers=["Location", "Nearest Neighbor", "Distance (km)", "Distance (miles)"],
    floatfmt=".1f"
))

if __name__ == "__main__":

    # your locations, tables, etc. above here

    # Compare Haversine and Geodesic distances
    y = haversine(
        41.494092, -81.796620,
        39.73682, -121.82390
    )

    x = calculate_distance(
        41.494092, -81.796620,
        39.73682, -121.82390
    )

    print(f"Haversine Distance: {y:.1f} km")
    print(f"Geodesic Distance: {x:.1f} km")