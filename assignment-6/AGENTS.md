# AGENTS.md
The goal of this assignment is to retrieve and analyze a seven-year time series from two very different kinds of big Earth data, and to do it within a fixed memory budget. Pixi task should be used to run code in end along with validation tests.

## What should the code do
Build a satellite time series of reservoir water area from Sentinel-2 imagery with stackstac and Dask Array, retrieve daily precipitation records from NOAA’s GHCN-D archive with Dask DataFrame

## Project structure
'''
pixi.toml           Environment and tasks
utils/              All python code for reprojection
test/               All test related scripts
notebook/           Example notebook that demos the utility of the reprojection module

'''

## Do's and Donts 
- only use python and no other language to implement module
- only use pixi for environment and package management
- src/utils.py will be only functions and contain no plots
- notebook is for visualiztion only
- do not create new files or edit REFLECTION.md
- the domain rules (GHCN-D Parquet on s3://noaa-ghcn-pds read anonymously, read only the years and columns needed, units and quality flags as documented in the GHCN-D readme)
- the memory rules (the cluster configuration is fixed, functions must return lazy Dask objects unless their result is small by construction, never call .compute() on unreduced data)
- run tests with pixi run test
- Unit tests should evaluate realistic examples 
- units test should fail if the test source code is changed
- Add detailed comments in the code and functions to help user interpret the code
- Use lazy Dask operations and avoid loading entire satellite or precipitation datasets into memory.
- Require meaningful unit tests, including edge cases, and make sure tests actually detect incorrect results
- PReserve Sentinel-2 processing baselines, cloud masks, coordinate systems, units, and missing-data handling.
- any scientific assumptions made should be outlined in comments.
- jupyter lab extension can be used to work within vsCODE application

# Pixi Environment

Use the existing pixi.toml environment configuration.

The project must work with the following activation setting:

[activation.env]
PYTHONPATH = "${PIXI_PROJECT_ROOT}"

Run Python code and tests through Pixi.

## Assumptions
- utility functions for imagery pipeline should not be changed without permission
- Sentinel 2 scenes will be used. 


## definition of done
- tests and code should be able to run with pixi tasks