# Legacy Waterdata Workflow Alignment Design

## Goal

Refocus the USGS waterdata demo notebook around the two legacy workflow themes shown in the sample files under `data/`:

- `Creating New Project`: bounding-box station discovery for `discharge`, `gw_daily`, and `gw_periodic`
- `Adding Data to Project`: station-based time-series retrieval for `discharge`, `gw_daily`, and `gw_periodic`

The notebook should keep using `dataretrieval.waterdata`, but it should present the modern calls in a way that clearly mirrors the old workflow patterns and their differences.

## Context

The current notebook already:

- keeps `dataretrieval.waterdata` usage inside the notebook
- loops all three workflow types for the legacy sections
- writes JSON, CSV, and parquet outputs for the add-data section
- includes one plot widget for generated time-series outputs

The new request changes the emphasis:

- treat the sample files in `data/` as the reference shape for the notebook sections
- explicitly note the differences in the old service-link patterns
- add one plotting widget per section
- keep `helpers/` support-only
- do not produce `.rdb` output files

## Reference Themes

The sample files show two distinct legacy themes:

### Creating New Project

Reference samples:

- `data/discharge_newproject.txt`
- `data/daily_new_project.txt`
- `data/perodic_newproject.txt`

These are site-discovery outputs with a shared site-metadata shape. The repeated themes are:

- `agency_cd`
- `site_no`
- `station_nm`
- `site_tp_cd`
- decimal latitude and longitude
- state, county, and other basic location metadata

The key difference between the legacy links is the filter logic, not the overall table shape:

- `discharge`: bbox site search with `siteType=ST`, `hasDataTypeCd=dv`, `parameterCd=00060`
- `gw_daily`: bbox site search with `siteType=GW`, `hasDataTypeCd=dv`
- `gw_periodic`: broader bbox site search without the daily-value filter

### Adding Data to Project

Reference samples:

- `data/discharge_add_data.txt`
- `data/daily_add_data.txt`

These are station-based time-series outputs. The repeated themes are:

- station id
- timestamp/date column
- primary value column
- qualification or grade information

The legacy retrieval patterns differ by workflow:

- `discharge`: daily values for a streamflow station
- `gw_daily`: daily values for a groundwater station
- `gw_periodic`: groundwater-level style station retrieval rather than a bbox site search

There is no periodic add-data sample file, so the notebook should infer that section from the provided legacy groundwater-level reference and the modern `waterdata` retrieval shape.

## Requirements

- Keep all `dataretrieval.waterdata` API usage inside the notebook
- Keep `helpers/usgs_waterdata_demo.py` support-only
- Add notebook notes that explain which legacy link pattern each modern call is replacing
- Do not write `.rdb` files
- Keep JSON, CSV, and parquet output writing only for the `Adding Data to Project` section
- Keep `Creating New Project` as a display-only discovery section with no file outputs
- Cover all three workflow types in both sections
- Add one plot widget per section

## Recommended Approach

Keep the notebook centered on two legacy-replacement sections, but make the section outputs and visuals intentionally different.

### Creating New Project

Use notebook-local bbox discovery logic that calls `dataretrieval.waterdata` directly and returns site tables shaped around the old site-file themes. Present the results as:

- one table per workflow type
- a workflow selector widget that renders a longitude/latitude station scatter for the selected workflow

This makes the section feel like the old station-discovery workflow instead of a generic data preview.

### Adding Data to Project

Use notebook-local station retrieval logic that calls `dataretrieval.waterdata` directly and returns normalized time-series payloads for export. Present the results as:

- one result per workflow type
- JSON, CSV, and parquet file paths
- a separate workflow selector widget that renders the selected time series with matplotlib

This preserves the current export flow while making the legacy station-based pattern clearer.

## Notebook Changes

### Legacy Workflow References

Add or update the explanatory text near the top of the notebook so it explicitly explains the old link differences:

- `Creating New Project` uses bbox site-discovery links for all three workflow types
- `discharge` and `gw_daily` add daily-value-oriented filters to the site search
- `gw_periodic` is broader at the site-discovery stage
- `Adding Data to Project` uses station-based pulls
- `discharge` and `gw_daily` follow daily-values style retrieval
- `gw_periodic` follows groundwater-level / field-measurement retrieval

### Creating New Project Section

Keep the section notebook-first and visible:

- notebook-local `get_usgs_stations_in_bbox(...)`
- notebook-local rendering logic that loops `discharge`, `gw_daily`, and `gw_periodic`
- display tables that emphasize the shared site-file columns from the legacy samples

Preferred visible columns include:

- `site_no`
- `station_nm`
- `site_tp_cd`
- `dec_lat_va`
- `dec_long_va`
- selected state/county metadata when present

### Creating New Project Plot Widget

Add a section-specific plotting widget for the bbox results:

- use `ipywidgets.Dropdown` for workflow selection
- plot station longitude vs latitude with matplotlib
- title should identify the selected workflow and the bbox-discovery purpose
- keep the plot lightweight and explanatory rather than styled as GIS output

### Adding Data to Project Section

Keep the section notebook-first and export-oriented:

- notebook-local `get_usgs_timeseries(...)`
- retrieval loop across `discharge`, `gw_daily`, and `gw_periodic`
- exported JSON, CSV, and parquet outputs for each workflow
- preview tables shaped around the add-data sample themes

Preferred visible columns include:

- station id
- `time`
- `value`
- qualification/status columns when available
- `unit_of_measure` when available

### Adding Data to Project Plot Widget

Keep a separate time-series widget for generated outputs:

- use `ipywidgets.Dropdown` for workflow selection
- reuse `add_data_results` so plotting does not trigger another retrieval
- plot `value` against `time`
- label the y-axis from `unit_of_measure` when available
- note in the section text that `gw_periodic` is intentionally different from the daily-value pulls

## Helper Boundaries

`helpers/usgs_waterdata_demo.py` should remain limited to support concerns such as:

- configuration constants
- mapping/reference rows used by the notebook
- artifact export utilities
- artifact message formatting

The helper module should not regain ownership of:

- bbox station discovery
- station-based `waterdata` retrievals
- section-level orchestration
- plotting helpers

## Error Handling

- If one bbox workflow returns no stations, show an empty preview and keep the other workflows rendering
- If one add-data workflow returns no rows, keep the other workflows rendering and skip its plot gracefully
- If export for one workflow fails, surface the message in that workflow’s result without breaking the whole notebook
- Keep the `gw_periodic` retrieval path explicitly separate from the daily-value path in both code comments and rendered notebook text

## Testing

Update notebook-focused tests to verify:

- the notebook references the legacy workflow-link differences
- the notebook defines both section-specific widgets
- the `Creating New Project` widget uses station-discovery results
- the `Adding Data to Project` widget uses generated add-data results
- all three workflow types appear in both sections

Keep helper tests focused on support behavior only, especially:

- JSON/CSV/parquet export writing
- export messaging
- geometry-safe JSON export behavior

## Verification

After implementation:

- execute `notebooks/usgs_waterdata_demo.ipynb`
- rerun `tests/test_usgs_waterdata_demo.py`
- confirm that:
  - `Creating New Project` renders bbox-based station tables for all three workflow types
  - `Creating New Project` includes the station-scatter widget
  - `Adding Data to Project` renders station-based results for all three workflow types
  - `Adding Data to Project` includes the time-series widget
  - JSON, CSV, and parquet files are still written only for the add-data section

## Out of Scope

- generating `.rdb` outputs
- recreating shapefiles, GIS layers, or BASINS base layers
- attempting to exactly duplicate the full legacy column inventory
- introducing a second dimension of widget controls beyond simple workflow selection
- moving `waterdata` retrievals back into `helpers/`
