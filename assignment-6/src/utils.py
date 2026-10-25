

from pystac_client import Client
import xarray as xr
import stackstac
import numpy as np

api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"

def search_items(bbox, start, end, max_cloud):
    """
    Search for items within a bounding box and time range, filtering by cloud cover.

    Returns:
    list: A list of items that match the search criteria.
    """
    client = Client.open(api_url)
    search= client.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cloud}}
    )
    return search.item_collections()

def dedupe_items(items, mgrs_tile):
    unique_items = {}
    for item in items:
        tile = item.properties["s2:mgrs_tile"]
        date = item.datetime.date()
        baseline = float(item.properties[s2:processing_baseline])

        # skip items from other tiles
        if tile !=mgrs_tiles:
            continue
        # keep the first image for date
        if data not in unique_items:
            unique_items[date] = item

        # other compare processing baseline
        else:
            old_item = unique_items[date]
            old_baseline = float(old_item.properties["s2:processing_baseline"])

            if baseline > old_baseline:
                unique_items[date] = item
    return unique_items.values()

def to_reflectance(stack):
    # convert a stack of DNs to SR, scene by scene, leaving scl band unchanged
    # get the processing baseline to each scene
    baseline=stack.coords["s2:processing_baseline"]
    # convert baseline strings to numbers
    baseline = baseline.astype(float)
    # select the reflectance bands
    reflectance = stack.sel(band=["green", "nir"])
    #apply offset
    offset= xr.where(baseline>= 4.0, 1000, 0)
    # convert dn to reflectance
    reflectance = (reflectance + offset)/ 10000
    # leave scl band unchanged
    scl = stack.sel(band="scl")

def stack_items(items, assets, bbox, resolution=20, epsg=32610):

    # translate common band names to sentinel-2 band names
    band_map = {
        "green": "B03",
        "nir": "B08",
        "scl": "SCL"
    }

    # get the STAC asset keys
    asset_keys = [band_map[band]for band in assets]

    # create the lazy stack
    stack = stackstac.stack(
        items,
        assets=asset_keys,
        resolution=resolution,
        epsg=epsg,
        bounds_latlon=bbox,
        dtype='float32',
        fill_value=np.float32(np.nan),
        rescale=False
    )
    # rename bands to common names
    stack = stack.assign_coords(band=assets)

    # conver dn to reflectance
    stack = to_reflectance(stack)
    return stack

def mask_clouds(stack, bad_classes=(0, 1, 3, 8, 9, 10)):

    #select the SCL band
    scl = stack.sel(band="scl")

    # identify pixels belonging to bad classes
    bad_pixels = scl.isin(bad_classes)

    # remove the SCL band
    reflectance = stack.sel(band=["green", "nir"])

    # replace bad pixels with NaN
    masked = reflectance.where(~bad_pixels)

    return masked

def ndwi(stack):
    # select corrected reflectance bands needed
    green = stack.sel(band="green")
    nir = stack.sel(band="nir")
    ndwi = (green - nir) / (green + nir)
    return ndwi

def water_area(ndwi, threshold=0.0):

    # Identify water pixels
    water_pixels = ndwi > threshold

    # Count the number of water pixels
    water_count = water_pixels.sum(dim=["x", "y"])

    # Calculate pixel area in square kilometers
    pixel_area = (
        np.abs(ndwi.x[1] - ndwi.x[0])
        * np.abs(ndwi.y[1] - ndwi.y[0])
        / 1000000
    )

    # Calculate total water area in square kilometers
    total_water_area = water_count * pixel_area

    # Count pixels that are not NaN
    valid_pixels = ndwi.notnull()

    # Calculate fraction of valid pixels
    valid_fraction = valid_pixels.mean(dim=["x", "y"])

    # Return both variables as a Dataset
    return xr.Dataset({
        "water_km2": total_water_area,
        "valid_fraction": valid_fraction
    })