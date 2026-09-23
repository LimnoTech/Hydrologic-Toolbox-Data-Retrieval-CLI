# Notebook-First Waterdata Demo Design

## Goal

Refactor the USGS waterdata demo so the notebook itself is the primary teaching
artifact for `dataretrieval.waterdata`.

The notebook should show the real API calls directly for both legacy workflow
sections:

1. `Creating New Project`
2. `Adding Data to Project`

The `helpers/` module should remain only a small support layer for shared
configuration, mapping metadata, and file-export utilities.

## Current State

- The notebook already renders the two legacy workflow sections and executes
  successfully end to end.
- The real `waterdata` retrieval logic still lives mostly in
  `helpers/usgs_waterdata_demo.py`.
- The notebook currently demonstrates orchestration, but it does not expose the
  actual `waterdata` usage clearly enough for a demo/tutorial purpose.
- `helpers/usgs_waterdata_demo.py` currently mixes:
  - demo config and mapping metadata
  - export helpers
  - direct `waterdata` retrieval functions
  - demo-specific retrieval orchestration support

## Requirements

1. The notebook must directly contain the demo functions that call
   `dataretrieval.waterdata`.
2. The `Creating New Project` section must define and use a notebook-local
   `get_usgs_stations_in_bbox(...)` function.
3. The `Adding Data to Project` section must define and use a notebook-local
   `get_usgs_timeseries(...)` function.
4. Any notebook function that uses `dataretrieval.waterdata` must include a
   short explanation of:
   - what `waterdata` function is being used
   - the important arguments
   - the expected return shape or purpose
5. `helpers/usgs_waterdata_demo.py` must no longer hide the main `waterdata`
   retrieval logic for the demo.
6. `helpers/usgs_waterdata_demo.py` should keep only support concerns that are
   still worth sharing across notebook cells and tests.
7. Existing demo behavior must remain intact:
   - station previews for `Creating New Project`
   - time-series previews for `Adding Data to Project`
   - JSON, CSV, and parquet exports for all three workflow types
8. The notebook must continue to support:
   - `discharge`
   - `gw_daily`
   - `gw_periodic`

## Assumption

This refactor favors readability and teaching value over strict DRY reuse. A
slightly longer notebook is acceptable if it makes the `waterdata` API usage
clearer and easier to learn from.

## Recommended Approach

Move the demo retrieval functions into the notebook, directly next to the
sections that use them, and trim the helper module down to config/mapping/export
support only.

This keeps the notebook honest as a demo of `dataretrieval.waterdata`, while
still preserving a small support module for shared constants and file-writing
utilities.

## Design

### Notebook responsibilities

The notebook should own all demo-visible `waterdata` usage.

It should define notebook-local functions for:

- station discovery in `Creating New Project`
- time-series retrieval in `Adding Data to Project`
- any notebook-specific normalization that exists only to support those API
  examples

The notebook should also add short explanatory notes near each API-using
function/cell so a reader can understand:

- which `waterdata` function is being used
- why it is used for that workflow
- what inputs matter most
- what the returned DataFrame is used for in the demo

### Creating New Project section

This section should contain the actual notebook-local
`get_usgs_stations_in_bbox(...)` function.

That function should show the real `waterdata` station-discovery calls needed
for:

- `discharge`
- `gw_daily`
- `gw_periodic`

Expected notebook behavior:

- call `get_monitoring_locations(...)`
- use `get_time_series_metadata(...)` where needed
- use `get_field_measurements(...)` where needed
- normalize/filter results for the three workflow types
- render station counts and previews only
- not write output files

### Adding Data to Project section

This section should contain the actual notebook-local
`get_usgs_timeseries(...)` function.

That function should show the real `waterdata` retrieval calls needed for:

- `discharge` via `get_daily(...)`
- `gw_daily` via `get_daily(...)`
- `gw_periodic` via `get_field_measurements(...)`

Expected notebook behavior:

- retrieve one configured example station per workflow type
- normalize the returned frame enough for export/rendering
- write JSON, CSV, and parquet artifacts using shared export helpers
- render frame previews and artifact paths in the notebook
- continue per workflow if one workflow errors

### Helper-module responsibilities

`helpers/usgs_waterdata_demo.py` should remain support-only.

Keep:

- `DEMO_CONFIG`
- `LEGACY_CALLS`
- `NOTEBOOK_MAPPING_ROWS`
- export helpers such as `export_timeseries_artifacts(...)`
- artifact-report formatting helpers such as `format_artifact_messages(...)`

Remove from helpers:

- `get_usgs_stations_in_bbox(...)`
- `get_usgs_timeseries(...)`
- workflow-specific station retrieval internals
- demo-only warning wrappers around `waterdata`
- demo-specific task/output builder helpers that only exist to support the
  notebook example

### Helpers folder cleanup

The `helpers/` folder should be cleaned so it reflects actual remaining support
responsibilities.

That means:

- remove demo retrieval logic that no longer belongs there
- keep `__init__.py` minimal and sensible
- avoid leaving dead wrappers or stale helper names behind

### Testing

Tests should shift their center of gravity from helper-owned retrieval behavior
to notebook-owned retrieval behavior.

Update tests to verify:

- the notebook defines the local retrieval functions
- the notebook contains explanatory API notes for `waterdata` usage
- the notebook-local station-discovery function handles the three workflow types
- the notebook-local time-series function handles the three workflow types
- `helpers/` no longer exports or owns the demo retrieval entry points
- export/file-format helper tests still pass for the utilities that remain in
  `helpers/`
- executed-notebook verification still proves:
  - both legacy sections render
  - all three workflows render
  - all three workflows write artifacts in the add-data section

## Out of Scope

- Reworking the legacy workflow goals themselves
- Reintroducing GIS, shapefile, or BASINS-specific steps
- Changing the configured stations or date ranges unless required by the
  notebook-local refactor
- General notebook restyling unrelated to making the API usage clearer
