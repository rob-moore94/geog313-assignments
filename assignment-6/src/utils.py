

from pystac_client import Client
import xarray as xr
import stackstac
import numpy as np
import calendar
from collections.abc import Iterable

import dask.dataframe as dd
import pandas as pd
from pyproj import Geod

api_url = "https://planetarycomputer.microsoft.com/api/stac/v1"
GHCN_PARQUET_TEMPLATE = (
    "s3://noaa-ghcn-pds/parquet/by_year/YEAR={year}/ELEMENT={element}/*.parquet"
)

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
    return search.item_collection()

def dedupe_items(items, mgrs_tile):
    unique_items = {}
    for item in items:
        tile = item.properties["s2:mgrs_tile"]
        date = item.datetime.date()
        baseline = float(item.properties["s2:processing_baseline"])

        # skip items from other tiles
        if tile !=mgrs_tile:
            continue
        # keep the first image for date
        if date not in unique_items:
            unique_items[date] = item

        # other compare processing baseline
        else:
            old_item = unique_items[date]
            old_baseline = float(old_item.properties["s2:processing_baseline"])

            if baseline > old_baseline:
                unique_items[date] = item
    return list(unique_items.values())

def to_reflectance(stack):
    # convert a stack of DNs to SR, scene by scene, leaving scl band unchanged
    # get the processing baseline to each scene
    baseline=stack.coords["s2:processing_baseline"]
    # convert baseline strings to numbers
    baseline = baseline.astype(float)
    # select the reflectance bands
    reflectance = stack.sel(band=["green", "nir"])
    # Baseline 04+ stores values with a +1000 DN offset; remove it before scaling.
    offset= xr.where(baseline>= 4.0, 1000, 0)
    # convert dn to reflectance
    reflectance = (reflectance - offset)/ 10000
    # leave scl band unchanged
    scl = stack.sel(band="scl")
    return reflectance, scl
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


def load_stations(url):
    """Read the fixed-width GHCN-D station inventory from ``url``.

    The station inventory is small enough to materialize as pandas data.  The
    fixed-width columns follow NOAA's ``ghcnd-stations.txt`` specification:
    station identifier, latitude, longitude, elevation, state, and name.
    """
    stations = pd.read_fwf(
        url,
        colspecs=[(0, 11), (12, 20), (21, 30), (31, 37), (38, 40), (41, 71)],
        names=["station", "latitude", "longitude", "elevation", "state", "name"],
        header=None,
        dtype={"station": "string", "state": "string", "name": "string"},
    )
    stations["station"] = stations["station"].str.strip()
    stations["name"] = stations["name"].str.strip()
    return stations


def stations_within(stations, lon, lat, radius_km):
    """Return stations within a geodesic radius, ordered by distance.

    ``pyproj.Geod.inv`` computes ellipsoidal distances in metres.  This avoids
    treating longitude and latitude degrees as if they were equal-distance
    Cartesian coordinates.
    """
    if radius_km < 0:
        raise ValueError("radius_km must be non-negative")

    geod = Geod(ellps="WGS84")
    _, _, distances_m = geod.inv(
        np.full(len(stations), lon, dtype=float),
        np.full(len(stations), lat, dtype=float),
        stations["longitude"].to_numpy(dtype=float),
        stations["latitude"].to_numpy(dtype=float),
    )
    result = stations.copy()
    result["distance_km"] = distances_m / 1000.0
    return result.loc[result["distance_km"] <= radius_km].sort_values(
        "distance_km"
    ).reset_index(drop=True)


def _column_name(columns, *candidates):
    """Find a schema column case-insensitively, with an explicit error."""
    by_lower = {str(column).lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in by_lower:
            return by_lower[candidate.lower()]
    raise ValueError(
        f"Required GHCN column not found; expected one of {candidates}, "
        f"found {list(columns)}"
    )


def load_ghcn(element, years):
    """Lazily load one GHCN-D element from the yearly Parquet copies.

    The initial read of each year's metadata provides the actual schema before
    column selection.  Only station, date, element, value, and quality flag
    columns are then read from S3; row filtering remains lazy.
    """
    if not isinstance(element, str) or not element:
        raise ValueError("element must be a non-empty string")
    years = (
        list(years)
        if isinstance(years, Iterable) and not isinstance(years, (str, bytes))
        else [years]
    )
    if not years:
        raise ValueError("years must contain at least one year")

    frames = []
    for year in years:
        path = GHCN_PARQUET_TEMPLATE.format(year=int(year), element=element)
        schema = dd.read_parquet(path, storage_options={"anon": True})
        columns = schema.dtypes.index
        station_col = _column_name(columns, "station", "station_id", "id")
        date_col = _column_name(columns, "date", "datetime")
        element_col = _column_name(columns, "element")
        value_col = _column_name(columns, "value", "data_value")
        qflag_col = _column_name(columns, "qflag", "q_flag", "quality_flag", "quality")
        selected = [station_col, date_col, element_col, value_col, qflag_col]
        frame = dd.read_parquet(
            path,
            columns=list(dict.fromkeys(selected)),
            storage_options={"anon": True},
        ).rename(
            columns={
                station_col: "station",
                date_col: "date",
                element_col: "element",
                value_col: "value",
                qflag_col: "qflag",
            }
        )
        frames.append(frame)

    return dd.concat(frames, interleave_partitions=True).loc[
        lambda frame: frame["element"] == element
    ]


def daily_values(ddf, station_ids):
    """Filter valid stations and convert GHCN tenths to physical units.

    GHCN-D quality flags are blank/null for observations that pass quality
    control.  Precipitation and snow quantities are stored in tenths of mm;
    temperature elements are stored in tenths of degrees Celsius.
    """
    station_ids = list(station_ids)
    if not station_ids:
        return ddf.loc[ddf["station"].isin([])]

    result = ddf.loc[
        ddf["station"].isin(station_ids)
        & (ddf["qflag"].isna() | (ddf["qflag"] == ""))
    ].copy()
    result["date"] = dd.to_datetime(result["date"], errors="coerce")
    result["value"] = result["value"] / 10.0
    return result.dropna(subset=["date", "value"])


def completeness(daily, start, end):
    """Compute each station's valid-observation fraction for an inclusive range."""
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    if end < start:
        raise ValueError("end must not precede start")
    days = (end - start).days + 1
    in_range = daily.loc[
        (daily["date"] >= start) & (daily["date"] <= end),
        ["station", "date"],
    ]
    observed = in_range.drop_duplicates().groupby("station").size().compute()
    return observed / days


def monthly_totals(daily_station, min_fraction=0.9):
    """Return monthly precipitation totals, masking incomplete months."""
    if not 0 <= min_fraction <= 1:
        raise ValueError("min_fraction must be between 0 and 1")

    values = daily_station[["date", "value"]].copy()
    values = values.drop_duplicates(subset=["date"])
    values["year"] = values["date"].dt.year
    values["month"] = values["date"].dt.month
    grouped = values.groupby(["year", "month"]).agg(
        total=("value", "sum"),
        observed=("date", "count"),
    ).compute()

    if grouped.empty:
        return pd.Series(dtype=float, name="monthly_total_mm")
    index = pd.DatetimeIndex(
        [
            pd.Timestamp(int(year), int(month), 1)
            for year, month in grouped.index
        ]
    )
    days_in_month = np.array(
        [calendar.monthrange(timestamp.year, timestamp.month)[1] for timestamp in index]
    )
    totals = grouped["total"].to_numpy(dtype=float)
    totals[grouped["observed"].to_numpy() / days_in_month < min_fraction] = np.nan
    return pd.Series(totals, index=index, name="monthly_total_mm").sort_index()