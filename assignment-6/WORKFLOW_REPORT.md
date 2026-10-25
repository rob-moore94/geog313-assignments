# Dask Workflow Summary

## Overview

The notebook builds a memory-conscious, seven-year environmental time series for the Folsom Reservoir area. It combines Sentinel-2 satellite imagery with NOAA GHCN-D precipitation observations while keeping large intermediate arrays lazy and limiting materialized results to small summaries.

## Workflow

1. **Start Dask once.** The notebook creates one `LocalCluster` with two workers, two threads per worker, and a 2 GiB memory limit per worker. The resulting four-worker GiB aggregate limit is fixed for reproducible execution and monitoring through the Dask dashboard.
2. **Search Sentinel-2 scenes.** The workflow queries Planetary Computer for scenes covering the reservoir bounding box from October 2018 through December 2025, filters by cloud cover, signs assets, restricts results to tile `10SFH`, and removes duplicate dates by retaining the highest processing baseline.
3. **Build a lazy imagery stack.** Only the green, NIR, and scene-classification (SCL) assets are loaded at 20 m resolution. Dask-backed arrays remain lazy while reflectance conversion, SCL cloud masking, NDWI calculation, and water-area reduction are defined.
4. **Reduce imagery.** Water pixels are identified from positive NDWI values. The notebook computes per-scene water area and valid-pixel fraction, filters scenes below the completeness threshold, and aggregates retained observations to monthly medians and scene counts.
5. **Load precipitation lazily.** GHCN-D PRCP Parquet data are read anonymously from NOAA S3 for the required years and columns. Candidate stations within 30 km are evaluated for completeness, the best station is selected, and daily tenths-of-millimeter values are converted to millimeters.
6. **Combine and analyze.** Monthly precipitation and satellite water-area summaries are joined, exported, plotted, and aggregated into October–September water years. A comparison with an intentionally unfiltered stack documents the memory savings from the constrained workflow.
7. **Close resources.** The notebook closes both the Dask client and cluster after all analysis and exports finish.

## Changes Made

The previous notebook contained an older, duplicate workflow that started a four-worker, 1 GiB-per-worker cluster and computed imagery before the numbered assignment steps. This caused redundant cluster creation, stale outputs, and excessive runtime/memory pressure. That workflow was removed. The required cluster configuration was moved to the first cell, old execution outputs were cleared, and explicit shutdown calls were added at the end. No utility-function behavior was changed.

Validation was completed with `pixi run test`; all seven tests passed.
