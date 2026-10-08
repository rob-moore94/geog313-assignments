AGENTS.md — Assignment 5

Project Overview - This project uses Python to analyze Sentinel-2 imagery over Fiji, focusing on coordinate reference systems (CRS), reprojection, and cloud-native geospatial processing.

Environment - This is a **Pixi-only project. Use "pixi" for all dependency management and command execution.Do not use pip or conda to install packages.

Analysis functions will be written in "src/utils.py". Functions should be pure, reusable, and contain no plotting code. "notebooks/analysis.ipynb" is for calling functions, displaying results, and visualization only. Do not create additional files unless explicitly requested. Do not modify "reflection.md". Do not change existing functions and without approval. Jupyter Lab extension can be used to access notebooks in VS CODE.

Geospatial criteria:
- Use the Earth Search STAC API: `https://earth-search.aws.element84.com/v1`.
- Search the sentinel-2-l2a collection.
- The area of interest (aoi) is defined in EPSG:4326.
- Always reproject the aoi into each Sentinel-2 scene's native CRS before reading raster pixels.
- Read only the AOI window from cloud-optimized GeoTIFFs (COGs), never the entire scene.
- Use the correct CRS and units for all spatial calculations. Confirm if unsure

Testing - Run tests using "pixi run test". All tests must pass before work is considered complete. Do not create arbitray testing loops.

Definition of Done - Correct functions have been created and added to "src/utils.py". The notebook imports and uses these functions. Sentinel-2 imagery is compiled and then clipped using the correct CRS and area calculations. Only the AOI window is read from the COG assets. NDVI is calculated correctly and nodata is handled. All tests pass using "pixi run test". Existing files and functions remain intact unless modifications were necessary.

