# WaterData Raw CSV Export Design

## Summary

Change the add-data CSV export contract so both the CLI and GUI write a reduced daily-values CSV with a metadata preamble built from raw API values. Keep the current workflow selection and retrieval behavior, but replace the plain `DataFrame.to_csv()` output with a custom CSV writer that combines one daily-values lookup with one time-series-metadata lookup.

## Goals

- Make add-data CSV exports include a two-line metadata header before the tabular body.
- Use raw Water Data API values for the header fields rather than app-normalized substitutes.
- Reduce the CSV body to `Daily values`, `Time`, `Approval status`, and `Qualifier`.
- Keep CLI and GUI behavior aligned by changing the shared add-data export path once.

## Non-Goals

- Changing JSON or parquet export contracts.
- Changing create-new-project exports.
- Adding user-selectable CSV schemas or toggles.
- Renaming header labels to normalized snake_case names.
- Replacing the current `dataretrieval`-based workflow logic.

## User-Facing Behavior

### Adding Data To Project

- `add-data` still retrieves daily or field-measurement data for the requested station and date range.
- The CSV artifact for daily workflows is no longer a full normalized frame dump.
- The CSV begins with two metadata lines:
  - one header-label line prefixed with `#`
  - one header-value line prefixed with `#`
- The body header is exactly:

```csv
Daily values,Time,Approval status,Qualifier
```

- The body rows come from the observation fields already returned by the daily-values response.

### CLI And GUI

- The CLI and GUI continue to print the same summary and artifact-path messages.
- Both interfaces pick up the new CSV format through the shared add-data workflow.
- No new user inputs are required.

## Export Shape

For a discharge station like `02225500`, the CSV should have this general shape:

```csv
# TS_ID,Parameter,Statistic,IV_TS_ID,Description,site_no
# 447f21c4ac494d2a94d69c5079c557c4,00060,00003,5759fde33ad545e8881d4fffdcda371f,"Discharge, cubic feet per second",USGS-02225500
Daily values,Time,Approval status,Qualifier
1740,1903-06-24,Approved,
```

## Header Mapping

Use raw API values for each metadata field:

- `TS_ID` = daily `time_series_id`
- `Parameter` = daily `parameter_code`
- `Statistic` = daily `statistic_id`
- `IV_TS_ID` = time-series-metadata `parent_time_series_id`
- `Description` = time-series-metadata `parameter_description`
- `site_no` = time-series-metadata `monitoring_location_id`

The body columns map directly from the daily observation frame:

- `Daily values` = `value`
- `Time` = `time`
- `Approval status` = `approval_status`
- `Qualifier` = `qualifier`

## Architecture

Use the existing shared add-data workflow in `timeseries.py` to gather both the observation frame and the time-series metadata needed for the CSV preamble, and use focused helpers in `exports.py` to write the custom CSV format.

### Responsibilities

#### `timeseries.py`

- Continue to own add-data workflow retrieval logic.
- Keep `get_daily(...)` for discharge and groundwater-daily row data.
- Add one `get_time_series_metadata(...)` lookup for the same station and parameter code to populate CSV header metadata.
- Pass both the reduced body frame and resolved header metadata into the export layer.

#### `exports.py`

- Replace the plain CSV `to_csv()` path for add-data exports with a custom writer for the new contract.
- Keep JSON and parquet writing behavior unchanged.
- Add helpers to:
  - reduce the export frame to the four requested columns
  - format metadata header rows
  - write the two `#` preamble lines plus the body header and rows

#### `cli.py` And `gui.py`

- Keep their current interaction flow unchanged.
- Continue to call the shared add-data path without duplicating formatting logic.

## Data Flow

1. Normalize the requested station id to the `USGS-...` form already expected by Water Data calls.
2. Call `get_daily(...)` to retrieve row-level observation data.
3. Call `get_time_series_metadata(...)` for the same monitoring location and parameter code.
4. Choose the metadata row that matches the exported daily series so the header values align with the body.
5. Build a reduced export frame with only `value`, `time`, `approval_status`, and `qualifier`.
6. Write the CSV preamble from the resolved metadata fields using raw API values.
7. Write the reduced body header and rows.
8. Continue writing JSON and parquet through the current paths.

## Row Selection Rules

- Prefer the metadata row whose `time_series_id` matches the daily frame `time_series_id`.
- If no exact metadata match is found, fall back to the first metadata row that matches the monitoring location and parameter code.
- If a metadata field is missing after fallback, write a blank value rather than failing the export.

## Error Handling

- Missing metadata should not prevent CSV export when daily observation rows were returned successfully.
- Blank strings should be written for any unresolved header field.
- Empty or null qualifiers should remain blank in the CSV body.
- If no daily rows are returned, the workflow may still write the metadata preamble and body header with no data rows, matching the request shape as closely as possible.
- Existing JSON/parquet error handling should remain unchanged.

## Testing Strategy

Add focused tests that verify:

- the metadata row resolution chooses the matching `time_series_id` when available
- the CSV preamble uses the exact header labels and raw API-derived values
- the CSV body is reduced to the four requested columns in the requested order
- qualifier blanks remain blank rather than turning into stringified null values
- CLI and GUI still report artifact paths and row counts normally through the shared path
- missing metadata fields fall back to blank values instead of raising export errors

## Risks And Mitigations

- The CSV format now depends on two Water Data lookups instead of one.
  - Mitigation: keep the second call narrow and reuse the same station and parameter filters.
- Metadata lookup may return multiple series for one station and parameter.
  - Mitigation: select the row whose `time_series_id` matches the daily frame before applying fallback behavior.
- A custom CSV writer can drift from the rest of the export layer if it is too specialized.
  - Mitigation: keep the helper small and scoped to the add-data CSV contract.

## Documentation Notes

- Update the package docs to explain that add-data CSV exports now contain a metadata preamble plus a reduced daily-values table.
- Document that header values come directly from Water Data API fields, including `site_no = monitoring_location_id`.
- Do not modify the CLI or GUI user prompts as part of this work.

## Acceptance Criteria

- Daily add-data CSV exports begin with:
  - `# TS_ID,Parameter,Statistic,IV_TS_ID,Description,site_no`
  - a corresponding `#` value line populated from API data
- The body header is exactly `Daily values,Time,Approval status,Qualifier`.
- The body contains only the four requested columns.
- `site_no` uses the raw API `monitoring_location_id` value such as `USGS-02225500`.
- CLI and GUI both produce the new CSV format through the shared export path.
- JSON and parquet export behavior remains unchanged.
