# Task 6 Waterdata Artifact Generation Design

## Goal

Make task 6 of the USGS Water Data demo actually retrieve data through
`dataretrieval.waterdata` and emit JSON, CSV, and parquet artifacts into the
configured output directory.

## Current State

- `helpers/usgs_waterdata_demo.py` already imports
  `from dataretrieval import waterdata as wd`.
- `get_usgs_timeseries(...)` already routes to `wd.get_daily(...)` or
  `wd.get_field_measurements(...)` and calls `export_timeseries_artifacts(...)`.
- The demo notebook is still a stub and does not currently execute a real task-6
  retrieval flow, so users do not reach the artifact-writing path.
- Tests currently validate helper-level export behavior, but they do not prove
  that the notebook surfaces the task-6 workflow end to end.

## Requirements

1. Task 6 must fetch data via `dataretrieval.waterdata`, not a placeholder path.
2. Running the task-6 flow must attempt to write JSON, CSV, and parquet files in
   `outputs/usgs_waterdata_demo`.
3. The notebook must make the saved artifact paths visible so the user can see
   what was created.
4. If parquet writing is unavailable because the engine is missing, JSON and CSV
   must still be written and the notebook must surface the parquet error clearly.
5. Existing station-discovery and timeseries helper contracts must remain
   compatible with the current tests.

## Recommended Approach

Implement the missing notebook task-6 flow and harden the helper so artifact
export is reliable when called from notebook code.

This approach keeps all service interaction inside the helper module, which
preserves one clear integration point with `dataretrieval.waterdata`. The
notebook becomes a thin demo layer that selects a configured example station,
calls the helper, previews the returned data, and displays the generated file
paths.

## Design

### Helper responsibilities

- Keep `get_usgs_timeseries(...)` as the single entry point for task-6
  retrievals.
- Normalize `output_dir` to a `Path` so notebook callers can safely pass either
  a string from `DEMO_CONFIG` or a `Path` object.
- Preserve the existing payload contract:
  - `frame`
  - `records`
  - `files`
  - `metadata`
- Continue exporting JSON and CSV before attempting parquet so partial success is
  preserved if parquet support is missing.

### Notebook responsibilities

- Add a task-6 section that:
  - resolves the project root and output directory
  - uses the configured `discharge` example station as the default task-6 path
    because it is the most representative daily-series retrieval in the demo
  - calls `get_usgs_timeseries(...)`
  - previews the returned frame
  - displays the artifact file paths and any parquet warning
- Use `DEMO_CONFIG["example_stations"]` so the demo stays centralized and easy
  to update.
- Keep the notebook aligned with the helper instead of duplicating waterdata
  calls inline.
- When `files` is empty because no records were returned, render a clear
  "no artifacts written" message instead of assuming file paths exist.
- When `files["parquet"]` is `None`, render the JSON and CSV paths plus the
  captured parquet error so the user can see the partial-success outcome.

### Error handling

- Unsupported workflow types should continue to raise `ValueError`.
- Empty service responses should continue returning the empty-frame payload with
  a warning in metadata.
- Missing parquet support should not fail the overall task-6 flow; the notebook
  should show that JSON and CSV were saved and that parquet could not be written.

### Testing

- Extend helper-focused tests only where needed for path normalization or
  artifact payload behavior.
- Add notebook-structure assertions that confirm the notebook now includes a
  task-6 retrieval flow using `get_usgs_timeseries(...)`, targets the
  configured `discharge` example station, and surfaces saved file information.
- Add at least one execution-level smoke test for the task-6 path by executing
  the notebook or its extraction target with mocked `waterdata` responses,
  verifying that JSON and CSV artifacts are written and that parquet failure is
  surfaced without breaking the flow.

## Out of Scope

- Refactoring unrelated demo tasks.
- Changing station-discovery behavior beyond what is needed to support task 6.
- Adding new workflow types beyond `discharge`, `gw_daily`, and `gw_periodic`.
