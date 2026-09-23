# Legacy XML Waterdata Notebook Sections Design

## Goal

Recreate the two legacy XML-driven workflow sections in the demo notebook using
`dataretrieval.waterdata`:

1. `Creating New Project`
2. `Adding Data to Project`

The notebook should replace the old discharge, groundwater daily, and
groundwater periodic retrieval calls with modern `waterdata` calls while
ignoring GIS layers, shapefiles, and other D4EM-only steps.

## Current State

- The helper module already supports:
  - station discovery in a bounding box
  - time-series retrieval
  - JSON, CSV, and parquet export
- The notebook currently demonstrates only a narrow discharge retrieval path.
- The notebook does not yet present the full legacy workflow structure as two
  explicit sections.
- The notebook does not yet loop all three workflow types for
  `Adding Data to Project`.

## Requirements

1. The notebook must be organized around two explicit sections that correspond
   to the legacy XML workflow:
   - `Creating New Project`
   - `Adding Data to Project`
2. `Creating New Project` must query station results for `discharge`,
   `gw_daily`, and `gw_periodic` within the configured bounding box.
3. `Creating New Project` must display tabular station results only and must
   not save output files.
4. `Adding Data to Project` must loop all three workflow types and retrieve
   time-series data for the configured example stations.
   - exactly one configured example station per workflow type
   - exactly three retrievals total in the combined section
5. `Adding Data to Project` must save JSON, CSV, and parquet artifacts when
   supported and must surface the saved file paths in the notebook.
6. The notebook-local orchestration helpers for the two sections must live in
   the notebook itself, not as new top-level workflow helpers in the helper
   module.
7. The existing helper module remains the low-level integration point for
   `waterdata` calls, normalization, and exports.

## Assumption

The notebook will keep Python-friendly configuration inputs such as
`bbox`, `example_stations`, and `output_dir`, while the notebook section names
and helper names mirror the old XML workflow for readability.

## Recommended Approach

Keep the low-level retrieval code in `helpers/usgs_waterdata_demo.py`, but add
two notebook-local orchestration helpers that make the notebook read like the
legacy workflow.

This keeps the notebook focused on the XML-to-modern mapping while preserving
testable retrieval and export behavior in the helper module.

## Design

### Notebook structure

The notebook should contain, in order:

1. Setup and config
2. Legacy-to-modern mapping summary
3. `Creating New Project` section
4. `Adding Data to Project` section

The notebook should read like a replacement for the old XML workflow rather
than a generic API demo.

### Notebook-local helpers

Add two local notebook helpers:

- `run_create_new_project_section(...)`
- `run_add_data_to_project_section(...)`

These helpers are notebook-local orchestration functions only. They should call
the existing helper-module functions instead of duplicating `waterdata` logic.

### Creating New Project section

This section replaces the legacy station-discovery portion of the XML workflow.

Behavior:

- Use the configured bounding box
- Query all three workflow types:
  - `discharge`
  - `gw_daily`
  - `gw_periodic`
- Call `get_usgs_stations_in_bbox(...)`
- Return a mapping of workflow type to station DataFrame
- Display row counts and small previews for each workflow type
- Do not save outputs in this section

### Adding Data to Project section

This section replaces the legacy time-series retrieval portion of the XML
workflow.

Behavior:

- Loop over all configured example stations in
  `DEMO_CONFIG["example_stations"]`
- Treat `DEMO_CONFIG["example_stations"]` as one example station per workflow
  type, not a nested many-stations-per-workflow batch
- For each workflow type, call `get_usgs_timeseries(...)`
- Reuse the helper-module artifact formatting logic for reporting file outputs
- Display:
  - the workflow type
  - a small preview of the returned frame
  - the saved JSON/CSV/parquet paths, or an explanatory warning

### Helper-module responsibilities

`helpers/usgs_waterdata_demo.py` should continue to own:

- station discovery calls
- time-series calls
- station-id normalization for `waterdata`
- export writing
- artifact message formatting

It should not gain new top-level orchestration helpers for the two legacy
sections.

### Error handling

- If a station-discovery workflow returns no rows, show an empty result and keep
  the notebook running.
- If a time-series workflow returns no rows, show the warning from the helper
  payload and report that no artifacts were written.
- If parquet support is unavailable, still write JSON and CSV and surface the
  parquet warning in the notebook.
- The notebook-local workflow loop should catch exceptions per workflow type,
  record the error for that workflow, and continue rendering the others.
- A failure in one workflow type must not prevent later workflow types from
  being displayed in the section output.

### Testing

Extend tests to verify:

- the notebook contains both legacy-replacement sections
- the notebook defines the two notebook-local orchestration helpers
- the `Adding Data to Project` section loops all three workflow types
- the `Adding Data to Project` section performs exactly one retrieval per
  workflow type
- the `Creating New Project` section uses station discovery without saving files
- the `Adding Data to Project` section surfaces artifact paths or warnings for
  each workflow
- the `Adding Data to Project` section handles a failure in one workflow type
  without preventing later workflow types from rendering
- existing helper tests still cover low-level station discovery, normalization,
  and export behavior

Retain at least one executed-notebook verification path that:

- runs the notebook end to end
- checks that both legacy-replacement sections render
- checks that the `Adding Data to Project` section shows output for all three
  workflow types
- checks that artifact paths or warnings are visible in the rendered notebook

## Out of Scope

- Recreating GIS layers or shapefile generation
- Reproducing D4EM base-layer download steps
- Supporting HUC08 folder logic
- Restoring ignored XML-only arguments such as `MinCount`
- Implementing a literal XML parser or XML execution engine
