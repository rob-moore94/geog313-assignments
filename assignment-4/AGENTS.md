This is a pixi-only project, never reccomend venv, conda, or pip. 

All analysis functions go in src/utils.py. The notebook is for visualization only. 

Do not edit or create reflection.md file. This is a simple project to retrieve data online using pooch, use xarray and numpy to a subset region and temporal interval from my main data, and then analyze and visualize data. 

Use the NOAA ERSST v6 sea-surface-temperature dataset with pooch workflow. Use cosine-of-latitude weighting when calculating spatial mean SST. Use 1991–2020 as the climatological baseline when calculating SST anomalies. Keep SST and SST-derived values in degrees Celsius (°C). Do not change these assumptions simply to simplify code or resolve an error.

The project root is identified in the pixi.toml alongside packages available and their dependencies. 

Codes should contain detailed annotations. Tests should be run with 'pixi run test'. 