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


def search_best_scene(point, date_range, max_cloud):
    from pystac_client import Client
    from shapely.geometry import mapping

    catalog = Client.open("https://earth-search.aws.element84.com/v1")
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects=mapping(point),
        datetime=date_range,
        query={"eo:cloud_cover": {"lt": max_cloud}},
    )
    items = list(search.items())
    return min(
        items,
        key=lambda item: float(item.properties["eo:cloud_cover"]),
        default=None,
    )


def clip_asset(item, asset_key, aoi_4326):
    import rioxarray
    from pyproj import Transformer
    from shapely.geometry import mapping
    from shapely.ops import transform

    asset = item.assets[asset_key]
    scene_crs = item.properties["proj:code"]
    transformer = Transformer.from_crs("EPSG:4326", scene_crs, always_xy=True)
    aoi_scene = transform(transformer.transform, aoi_4326)

    raster = rioxarray.open_rasterio(asset.href, masked=True)
    return raster.rio.clip(
        [mapping(aoi_scene)],
        crs=scene_crs,
        from_disk=True,
    )


def ndvi(red, nir):
    import numpy as np

    def mask_nodata(values):
        nodata = values.attrs.get("_FillValue", values.attrs.get("nodata"))
        if nodata is None:
            try:
                nodata = values.rio.nodata
            except (AttributeError, ValueError):
                nodata = None
        return values if nodata is None else values.where(values != nodata)

    red = mask_nodata(red)
    nir = mask_nodata(nir)
    denominator = nir + red
    valid = np.isfinite(red) & np.isfinite(nir) & (denominator != 0)
    return ((nir - red) / denominator).where(valid).clip(-1, 1)