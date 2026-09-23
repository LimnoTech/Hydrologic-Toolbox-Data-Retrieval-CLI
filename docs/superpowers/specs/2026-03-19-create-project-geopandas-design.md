# Create Project GeoPandas Design

## Goal

Refine the USGS waterdata demo notebook so the `Creating New Project` section is the clear home for bounding-box station discovery, station previews, and the station-selection widget, while `Adding Data to Project` stays focused on station-based retrieval plus JSON/CSV/parquet export.

The `Creating New Project` section should use GeoPandas-backed station results so the notebook can show that the discovered stations carry GIS-style geometry and CRS metadata directly in memory without writing shapefiles.

## Context

The current notebook already:

- uses notebook-local `dataretrieval.waterdata` calls for station discovery and add-data retrieval
- keeps output artifact writing in the add-data workflow
- renders a station widget for the create-project flow and a time-series widget for the add-data flow
- keeps support plotting and widget helpers in `helpers/usgs_waterdata_demo.py`

The new request sharpens the create-project story:

- keep the streamgage/bounding-box widget in `Creating New Project`
- continue the preview tables that were already in place
- use GeoPandas for the bbox station results
- demonstrate GIS-style capability through `GeoDataFrame` behavior such as `gdf.crs`
- do not create shapefiles
- keep JSON/CSV/parquet output generation in `Adding Data to Project`

## Requirements

- `Creating New Project` must remain the place where bbox-discovered stations are shown and explored
- `Creating New Project` must continue to preview all three workflow types:
  - `discharge`
  - `gw_daily`
  - `gw_periodic`
- The bbox station results should be materialized as `GeoDataFrame`s
- The station `GeoDataFrame`s should expose CRS metadata so the notebook can show `gdf.crs`
- The create-project section should continue showing the existing preview tables, not replace them with only plots
- The create-project widget should stay in that section, not migrate into add-data behavior
- `Adding Data to Project` should continue to:
  - loop all three workflows
  - show time-series previews
  - write JSON/CSV/parquet outputs
- Export behavior should remain output-friendly even when the source frame includes geometry-bearing data
- No shapefiles or `.rdb` files should be produced

## Recommended Approach

Use a hybrid structure:

- `Creating New Project` produces `GeoDataFrame`s for station discovery and uses them for previews and the station map widget
- `Adding Data to Project` remains tabular and artifact-oriented
- shared helper support continues to handle geometry-aware normalization and export flattening

This keeps the legacy workflow split easy to understand:

- create-project answers “which stations are available in this area?”
- add-data answers “get the records for this station and save outputs”

## Create Project Design

The notebook-local `get_usgs_stations_in_bbox(...)` function should still own the visible `waterdata` calls, but its normalized outputs should become `GeoDataFrame`s instead of plain pandas `DataFrame`s.

Each workflow result should:

- preserve the legacy-style preview columns already shown in the notebook
- include a `geometry` column with point geometries built from station longitude/latitude
- use CRS `EPSG:4326`
- remain suitable for the existing create-project widget rendering

The rendered notebook should continue to show the preview table for each workflow type. In addition, it should make it obvious that the returned object is a `GeoDataFrame` with accessible CRS metadata, for example by showing the object type and `gdf.crs` value alongside the preview.

This is enough to demonstrate GIS-style payload support without creating shapefiles. The key point is that the notebook shows the in-memory object already carries the geometry and CRS information that a GIS workflow would need.

## Add Data Design

`Adding Data to Project` should remain station-based and export-focused.

That section should keep:

- the existing loop over `discharge`, `gw_daily`, and `gw_periodic`
- dataframe previews for each retrieved time-series result
- JSON/CSV/parquet output writing into `outputs/usgs_waterdata_demo`
- the add-data plot widget

The bbox station-discovery preview and station widget should not move into this section.

## Helper Responsibilities

`helpers/usgs_waterdata_demo.py` should continue to own support-only behavior such as:

- station normalization that can return geometry-ready data
- widget rendering for the create-project and add-data selectors
- plotting support for station maps and time-series plots
- export flattening for geometry-bearing frames
- artifact-message formatting

GeoPandas-specific frame creation can live either in the notebook or in helper support, but the direct `waterdata` API calls should remain visible in the notebook because this is still a demo.

## Dependencies

Add `geopandas` as a notebook/runtime dependency so the create-project station results can be built and displayed as `GeoDataFrame`s with CRS metadata.

## Testing

Update tests so they verify:

- the create-project workflow returns `GeoDataFrame` station results
- create-project results expose `geometry` and CRS metadata
- preview behavior still covers all three workflows
- the create-project widget still renders from the create-project results
- add-data behavior still loops all three workflows and writes outputs
- geometry-bearing export behavior remains safe for JSON/CSV/parquet output

## Verification

After implementation:

- rerun `tests/test_usgs_waterdata_demo.py`
- execute `notebooks/usgs_waterdata_demo.ipynb`
- confirm the notebook shows:
  - create-project preview tables for all three workflows
  - create-project station widget in the `Creating New Project` section
  - visible GeoPandas/CRS evidence such as `GeoDataFrame` type and `gdf.crs`
  - add-data previews and JSON/CSV/parquet outputs for all three workflows

## Out of Scope

- writing shapefiles
- writing `.rdb` files
- moving add-data export into the create-project section
- hiding the actual `waterdata` retrieval calls in helpers
- removing the existing preview tables
