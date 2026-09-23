# Pure-Python Shapefile Writer Fix Design

## Goal

Fix the packaged Windows executable so `create-new-project` can write shapefiles without requiring Fiona, pyogrio, or GDAL at runtime.

## Root Cause

- The current shapefile export path calls `GeoDataFrame.to_file(...)`.
- GeoPandas delegates shapefile writing to `pyogrio` or `fiona`.
- The Windows executable does not bundle a working GDAL-backed writer stack, so the `.exe` fails at runtime even though the Python workflow works locally.

## Approved Fix

- Replace the current `to_file(...)` shapefile export with a pure-Python writer.
- Add `pyshp` as the runtime dependency for shapefile creation.
- Keep the existing GeoDataFrame normalization and reduced-schema logic.
- Continue writing:
  - `.shp`
  - `.shx`
  - `.dbf`
  - `.prj`
  - `.cpg`

## Scope

- Keep the current CLI contract exactly as implemented.
- Keep the current reduced shapefile field set exactly as implemented.
- Do not change `add-data` CSV behavior.
- Update docs to note that the packaged shapefile export no longer relies on Fiona/pyogrio/GDAL.

## Verification

- Unit test the shapefile export helper using the pure-Python writer.
- Re-run the package test file.
- Re-run live `create-new-project` smoke tests.
- Confirm the output directory contains a valid shapefile set and no runtime import error occurs.
