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
    subset = ds.sel(
        lat = slice(lat_bounds[0], lat_bounds[1]),
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