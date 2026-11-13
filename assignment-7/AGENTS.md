# AGENTS.md

## Project Overview

This assignment analyzes Fields of The World (FTW) agricultural field boundaries for France and Kenya using GeoParquet and Dask-GeoPandas. The goal is to perform efficient geospatial analysis while minimizing memory usage.

## Project rules

- Use Python and Pixi exclusively for coding, environments, and package management.
- All analysis functions belong in `src/utils.py` and should be pure, except necessary data downloading and caching
- `src/utils.py` must not contain plots. The notebook is for visualization and demonstrating functions.
- Do not create unnecessary files or edit `reflection.md`.
- Preserve existing working functions unless changes are necessary.
- Add clear comments explaining code and scientific assumptions

## Data and Memory Rules

- FTW GeoParquet geometries use `EPSG:4326`.
- Calculate polygon areas in a projected CRS, not geographic coordinates.
- Confidence values range from 0 to 100.
- Filter France and Kenya to the same prediction year.
- Use Dask-GeoPandas and maintain lazy operations whenever possible.
- Only call `.compute()` for small final results; never compute entire country datasets.
- Avoid loading large datasets into pandas or GeoPandas.
- Do not commit downloaded GeoParquet files or temporary data to Git.

## Testing

- Run tests using `pixi run test`.
- Include meaningful unit tests and edge cases.
- Tests should detect incorrect results, not simply verify that code runs.
- Do not modify tests just to make them pass.

## Definition of Done

- Required functions will be implemented in `src/utils.py`.
- Notebook visualizations and comparisons work correctly.
- CRS, area, confidence, and year-filtering rules are followed.
- Dask processing remains memory-efficient.
- All tests pass with `pixi run test`.
- Existing functionality is preserved and no unnecessary files are created.