# CRS and cloud-native processing report

## CRS logic

The AOI is defined as a Shapely polygon in EPSG:4326, where coordinates are longitude and latitude in degrees. The Sentinel-2 scene selected for this run uses EPSG:32701, a projected UTM CRS with metre units. Before reading either raster asset, the workflow transforms the AOI from EPSG:4326 into the scene CRS using `Transformer.from_crs(..., always_xy=True)`. `clip_asset` then passes the transformed geometry to `rioxarray.rio.clip(..., from_disk=True)`, so only the AOI window is requested from the remote asset.

The AOI true area is not calculated in geographic degrees. It is reprojected into the equal-area CRS defined in Part 1 and divided by 1,000,000 to report square kilometres. The result for this run is 247.639141 km².

The NDVI result is mapped after reprojection to EPSG:4326 with Cartopy's Plate Carrée display projection centered at longitude 180. This keeps the Fiji/date-line region in the intended map frame rather than splitting it at the conventional -180/180 boundary.

## Mistakes found and corrected

1. The first notebook search used 2025-01-01 through 2026-10-08 with a 20% cloud limit and returned no items. The search was corrected to the available recent archive range 2023-01-01 through 2026-10-08 with a 10% limit; it selected a 3.20267% cloud scene from 2023-06-27.
2. The first raster read failed because the public Earth Search assets were JP2 files and the Pixi GDAL environment lacked the JP2OpenJPEG driver. The dependency `libgdal-jp2openjpeg` was added through Pixi, and the notebook enables anonymous public S3 access with `AWS_NO_SIGN_REQUEST=YES`.
3. A CRS error to avoid is clipping the EPSG:4326 AOI directly against a projected raster. Longitude and latitude degrees would then be interpreted as metre coordinates, producing an empty or displaced window. The reusable clipping function corrects this by reprojecting the AOI into each scene's native `proj:code` first.

## Timing

For the selected scene, the notebook reported an AOI-window read time of 58.276 seconds and a full red-asset read time of 15.327 seconds. The full read loaded an array of shape `(1, 10980, 10980)` and is included only as a benchmark; the production red, NIR, and NDVI workflow reads the AOI windows.
