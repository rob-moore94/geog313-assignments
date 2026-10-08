import pyproj

def describe_crs(crs_input):
    crs = pyproj.CRS.from_user_input(crs_input)
    # pull metadata
    epsg_code = crs.to_epsg()
    epsg_str = f"EPSG:{epsg_code}" if epsg_code else "Unknown EPSG"
    wkt_str = crs.to_wkt(pretty=True)
    proj_str = crs.to_proj4()
    datum_str = crs.datum.name if crs.datum else "Unknown Datum"
    units_str = crs.axis_info[0].unit_name if crs.axis_info else "Unknown Units"

    print(f"CRS Name: {crs.name}")
    print(f"EPSG Code: {epsg_str}")
    print(f"WKT: {wkt_str}")
    print(f"PROJ.4: {proj_str}")
    print(f"Datum: {datum_str}")
    print(f"Units: {units_str}")

    return {
        "name": crs.name,
        "epsg_code": epsg_str,
        "wkt": wkt_str,
        "proj4": proj_str,
        "datum": datum_str,
        "units": units_str
    }


def utm_epsg(lon, lat):
    # given a longitude and latitude return the UTM Zone and EPSG code
    zone_number = int((lon + 180) / 6) + 1
    hemisphere = 'north' if lat >= 0 else 'south'
    epsg_code = 32600 + zone_number if hemisphere == 'north' else 32700 + zone_number
    return zone_number, hemisphere, epsg_code

def reproject_geometry(geom, src_crs, dst_crs):
    import shapely.ops
    from shapely.geometry import shape, mapping 
    from pyproj import Transformer

    # create a transformer object
    transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
    # reproject the geometry
    reprojected_geom = shapely.ops.transform(transformer.transform, geom)
    return reprojected_geom

def shift_to360(geom):
    # return a geometry with longitudes shifted to the 0-360 range
    # (a longitude of -178.3 becomes 181.7), so that a shape crossing the antimeridian becomes contiguous.
    from shapely.ops import transform
    def shift_longitude(x, y, z=None):
        if x < 0:
            x += 360
        return (x, y) if z is None else (x)
        if z is None:
            return (x, y)
        return (x, y, z)

    return transform(shift_longitude, geom)

def projected_area_km2(geom, target_crs):
    # calculate the area of a geometry in square kilometers after reprojecting to a projected CRS
    from shapely.ops import transform
    from pyproj import Transformer

    # create a transformer to the target projected CRS
    transformer = Transformer.from_crs(geom.crs, target_crs, always_xy=True)
    # reproject the geometry
    projected_geom = transform(transformer.transform, geom)
    # calculate area in square meters and convert to square kilometers
    area_m2 = projected_geom.area
    area_km2 = area_m2 / 1e6
    return area_km2