import pooch
import xarray as xr
import numpy as np

# use pooch to retrieve to lo
def load_sst():
    url = "https://raw.githubusercontent.com/HamedAlemo/advanced-geo-python/main/files/noaa.ersst.v6/sst.mnmean.nc"
    file = pooch.retrieve(
        url=url,
        known_hash = "ef61d97774bda4cc21324a8ce33059ac826101590c0da9911ec1ceb8bcf357b7")
    ds = xr.open_dataset(file, drop_variables="time_bnds")
    return ds

# define subset region
def subset_region(ds, lat_bounds, lon_bounds):
    lat_slice = (
        slice(lat_bounds[0], lat_bounds[1])
        if ds.lat[0] < ds.lat[-1]
        else slice(lat_bounds[1], lat_bounds[0])
    )
    subset = ds.sel(
        lat = lat_slice,
        lon = slice(lon_bounds[0], lon_bounds[1]))
    return subset

# define temporal interval
def monthly_climatology(da, baseline=("1991", "2020")):

    # select baseline years
    baseline_da = da.sel(
        time=slice(baseline[0], baseline[1]))
    # group by month
    climatology = baseline_da.groupby("time.month").mean("time")

    return climatology
    
# function to calculatate anomalies
def anomalies(da, clim):
    anomaly = da.groupby("time.month") - clim
    return anomaly

# area weighted means
def area_weighted_mean(da):
    weights = np.cos(np.deg2rad(da.lat))
    weighted_means = da.weighted(weights).mean(dim=["lat","lon"])
    return weighted_means


def rolling_index(anom_series: xr.DataArray, window: int = 3) -> xr.DataArray:
    """Calculate a centered rolling mean of an area-averaged anomaly series.

    Parameters
    ----------
    anom_series : xr.DataArray
        Area-averaged SST anomalies indexed along the ``time`` dimension.
    window : int, default=3
        Number of time steps included in each rolling mean.

    Returns
    -------
    xr.DataArray
        The centered rolling anomaly index. Values at the edges are missing
        when a complete rolling window is not available.
    """
    return anom_series.rolling(time=window, center=True).mean()


def detect_events(
    index: xr.DataArray,
    threshold: float = 0.5,
    min_months: int = 3,
) -> dict[str, list[dict[str, object]]]:
    """Detect contiguous warm and cold events in an anomaly index.

    Parameters
    ----------
    index : xr.DataArray
        Monthly anomaly index with a ``time`` dimension.
    threshold : float, default=0.5
        Absolute anomaly threshold in degrees Celsius. Warm events meet or
        exceed this value, while cold events are at or below its negative.
    min_months : int, default=3
        Minimum number of consecutive months required for an event.

    Returns
    -------
    dict[str, list[dict[str, object]]]
        A dictionary with ``warm`` and ``cold`` event lists. Each event has
        ``start`` and ``end`` dates and a signed ``peak`` magnitude in
        degrees Celsius.
    """
    if min_months < 1:
        raise ValueError("min_months must be at least 1")

    events: dict[str, list[dict[str, object]]] = {"warm": [], "cold": []}
    times = index.time.values
    values = index.values
    active_kind: str | None = None
    active_start = 0
    active_values: list[float] = []

    def finish_event(end_position: int) -> None:
        if active_kind is None or len(active_values) < min_months:
            return

        peak = max(active_values) if active_kind == "warm" else min(active_values)
        events[active_kind].append(
            {
                "start": times[active_start],
                "end": times[end_position],
                "peak": peak,
            }
        )

    for position, value in enumerate(values):
        if np.isfinite(value) and value >= threshold:
            kind = "warm"
        elif np.isfinite(value) and value <= -threshold:
            kind = "cold"
        else:
            kind = None

        if kind != active_kind:
            finish_event(position - 1)
            active_kind = kind
            active_start = position
            active_values = []

        if kind is not None:
            active_values.append(float(value))

    finish_event(len(values) - 1)
    return events


def composite(
    anom_field: xr.DataArray,
    event_months: xr.DataArray | np.ndarray | list[object],
) -> xr.DataArray:
    """Calculate a spatial anomaly composite over selected event months.

    Parameters
    ----------
    anom_field : xr.DataArray
        Monthly anomaly field with a ``time`` dimension and spatial
        dimensions such as ``lat`` and ``lon``.
    event_months : xr.DataArray, np.ndarray, or list
        Time-coordinate values identifying the months to include in the
        composite.

    Returns
    -------
    xr.DataArray
        The mean anomaly field across the selected event months, with the
        ``time`` dimension removed.
    """
    selected_anomalies = anom_field.sel(time=event_months)
    return selected_anomalies.mean(dim="time")


def coarsen_to_4deg(field: xr.DataArray) -> xr.DataArray:
    """Create a 4-degree anomaly map by averaging neighboring 2-degree cells.

    Parameters
    ----------
    field : xr.DataArray
        Anomaly field with 2-degree ``lat`` and ``lon`` dimensions.

    Returns
    -------
    xr.DataArray
        The field coarsened to approximately 4-degree resolution. Incomplete
        edge blocks are excluded from the mean.
    """
    return field.coarsen(lat=2, lon=2, boundary="trim").mean()


def interp_to_4deg(field: xr.DataArray) -> xr.DataArray:
    """Create a 4-degree anomaly map by interpolating the 2-degree field.

    Parameters
    ----------
    field : xr.DataArray
        Anomaly field with 2-degree ``lat`` and ``lon`` dimensions.

    Returns
    -------
    xr.DataArray
        The field interpolated onto every second latitude and longitude
        coordinate of the input field.
    """
    return field.interp(lat=field.lat[::2], lon=field.lon[::2])


def linear_trend(anom_field: xr.DataArray) -> xr.DataArray:
    """Calculate the per-pixel linear anomaly trend in degrees per decade.

    Parameters
    ----------
    anom_field : xr.DataArray
        Anomaly field with monthly datetime values along the ``time``
        dimension and spatial dimensions such as ``lat`` and ``lon``.

    Returns
    -------
    xr.DataArray
        The degree-one polynomial coefficient for each spatial pixel,
        expressed in degrees Celsius per decade.
    """
    time_years = anom_field.time.dt.year + (anom_field.time.dt.month - 1) / 12
    field_in_years = anom_field.assign_coords(time=time_years)
    coefficients = field_in_years.polyfit(dim="time", deg=1)
    return coefficients["polyfit_coefficients"].sel(degree=1) * 10