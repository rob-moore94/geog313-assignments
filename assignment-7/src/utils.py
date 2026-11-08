import pandas as pd
import os
import requests
import dask_geopandas as dgpd

data_source = "https://data.source.coop/ftw/global-data/predictions/vectors/alpha/results-by-admin-conf/"
# download the FTW GeoParquet for one country from the path above
#  and cache it locally, skipping the download if the file already exists.
def get_country_fields(country_code, country_name, dest_dir):
    
    # Create the designated directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)
    # Construct the file path for the cached file
    file_path = os.path.join(
        dest_dir, f"{country_code}_{country_name}.parquet"
    )
    # Check if the file already exists
    if os.path.exists(file_path):
        print(f"File already exists: {file_path}. Skipping download.")
        return file_path

    # download data if it doesn't exist locally
    url = (
        f"{data_source}admin:country_code={country_code}./"
        f"{country_name}/results.parquet"
    )

    response = requests.get(url, timeout=120)
    response.raise_for_status()  # Raise an error for bad responses

    # save file locally
    with open(file_path, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded and cached file: {file_path}")
    return file_path
# load the country file lazily into Dask-Geopandas and return lazy object
def load_fields(path):
    return dgpd.read_parquet(path, split_row_groups="adaptive")

# for a small sample of n fields, compute the area compute the area
# by reprojecting to an appropriate equal-area or UTM CRS, and compare it 
# against the provided metrics:area. 
# Return both so the notebook can show they agree.
def verify_area(gdf, n=10):
    # select a small sample of n fields
    sample_gdf = gdf.get_partition(0).head(n)

    # estimate the appropriate UTM zone for the sample fields
    target_crs = sample_gdf.estimate_utm_crs()
    # reproject the sample fields to the target CRS
    projected_gdf = sample_gdf.to_crs(target_crs)
    # compute the area in square meters
    sample_gdf['computed_area'] = projected_gdf.geometry.area
    # return a comparison
    comparison = sample_gdf[['computed_area', 'metrics:area']]
    return comparison
