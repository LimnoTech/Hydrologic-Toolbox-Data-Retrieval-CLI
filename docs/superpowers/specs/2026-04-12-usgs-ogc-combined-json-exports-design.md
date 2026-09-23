# USGS OGC Combined JSON Exports Design

## Summary

Change the CLI and GUI export contract so both workflows write JSON artifacts that look like pasted-together USGS-style `FeatureCollection` responses instead of the current flattened pandas records array. Preserve the current app behavior for workflow logic, row counts, and CSV/parquet outputs, but build the JSON artifact from `dataretrieval` frames so the implementation stays within the required library boundary.

## Goals

- Make `add-data` write one combined JSON file per run that preserves a USGS-style `FeatureCollection` payload structure.
- Make `create-new-project` write one combined JSON file per workflow run that preserves a USGS-style `FeatureCollection` payload structure.
- Keep the JSON output close to the two USGS URLs the user provided rather than writing a synthetic tabular records export.
- Keep CSV and parquet export behavior intact.
- Keep CLI and GUI interaction flow unchanged apart from the contents of the JSON artifact.

## Non-Goals

- Replacing the existing DataFrame-based workflow logic for the whole app.
- Removing CSV or parquet export.
- Making the app offline-capable.
- Introducing multiple JSON export formats or a user-selectable toggle.
- Preserving the old flattened JSON structure.

## User-Facing Behavior

### Adding Data To Project

- `add-data` writes one JSON file for the requested station/workflow run.
- The JSON file contains one top-level object that combines:
  - a `monitoring_locations` `FeatureCollection` reconstructed from `dataretrieval.get_monitoring_locations(...)`
  - a `timeseries` `FeatureCollection` reconstructed from `dataretrieval.get_daily(...)` or `dataretrieval.get_field_measurements(...)`
- The JSON is not flattened into a list of records.
- CSV and parquet are still written from the normalized DataFrame path.

### Creating New Project

- `create-new-project` writes one JSON file per workflow run.
- Each JSON file contains one top-level object that combines:
  - a `monitoring_locations` `FeatureCollection` reconstructed from the candidate monitoring-location frame
  - a qualifying `FeatureCollection` reconstructed from the time-series-metadata or field-measurements frame
- The combined JSON is filtered to the same matched station ids the workflow currently keeps after intersecting candidate and qualifying results.
- The export is one file per workflow run, not one file per station.

## Export Shape

### Adding Data To Project

The JSON artifact should have this general shape:

```json
{
  "workflow_type": "discharge",
  "requested_at": "2026-04-12T12:34:56Z",
  "monitoring_locations": { "...raw FeatureCollection..." },
  "timeseries": { "...raw FeatureCollection..." }
}
```

### Creating New Project

The JSON artifact should have this general shape:

```json
{
  "workflow_type": "discharge",
  "requested_at": "2026-04-12T12:34:56Z",
  "monitoring_locations": { "...raw FeatureCollection..." },
  "qualifying_timeseries_metadata": { "...raw FeatureCollection..." }
}
```

- For `gw_periodic`, the second block should be `field_measurements` instead of `qualifying_timeseries_metadata`.
- The nested blocks should remain `FeatureCollection` objects rather than being collapsed into custom arrays.
- The top-level wrapper may add app-specific metadata such as `workflow_type` and `requested_at`, but it should not rewrite the nested blocks into a tabular records schema.

## Architecture

Use focused helpers in `exports.py`, `timeseries.py`, and `station_discovery.py` to convert `dataretrieval` frames into `FeatureCollection` objects for JSON artifacts.

### Responsibilities

#### `station_discovery.py`

- Continue to own the `create-new-project` workflow logic.
- Keep the current DataFrame-based discovery and qualifying logic for workflow behavior.
- Convert candidate and qualifying `dataretrieval` frames into filtered `FeatureCollection` blocks for export.

#### `timeseries.py`

- Continue to own the `add-data` workflow logic.
- Keep the current DataFrame-based retrieval path for app behavior and CSV/parquet export.
- Convert the station-monitoring-location and observation frames into `FeatureCollection` blocks for the JSON artifact.

#### `exports.py`

- Add support for converting frames into `FeatureCollection` objects and writing the new combined JSON object.
- Keep CSV/parquet writing on the current DataFrame path.
- Keep artifact message formatting unchanged except for whatever filename changes are needed.

## Data Flow

### Adding Data To Project

1. Normalize station id to the `USGS-...` form.
2. Run the current workflow retrieval logic to get the DataFrame used elsewhere in the app.
3. Fetch the monitoring-location frame through `dataretrieval`.
4. Convert the monitoring-location and timeseries frames into `FeatureCollection` objects.
5. Write one combined JSON object containing both raw blocks.
6. Continue writing CSV and parquet from the normalized DataFrame.

### Creating New Project

1. Run the current candidate and qualifying discovery logic to determine the matched stations.
2. Reuse the candidate and qualifying frames already returned by `dataretrieval`.
3. Filter those frames down to the same matched station ids already selected by the workflow.
4. Convert the filtered frames into `FeatureCollection` blocks.
5. Write one combined JSON object for that workflow run.

## Error Handling

- The JSON artifact should always be valid UTF-8 JSON with a stable top-level wrapper shape.
- `add-data` may write a combined JSON object with an empty `timeseries.features` list when the station request succeeds but no records are returned.
- `create-new-project` may write a combined JSON object with empty filtered feature collections when no stations qualify.
- Existing CSV/parquet error handling should remain unchanged.

## Testing Strategy

Add focused tests that verify:

- the frame-to-`FeatureCollection` helpers preserve the expected geometry and properties
- the combined JSON artifact preserves nested `FeatureCollection` blocks
- `add-data` writes the new combined JSON instead of a flattened records array
- `create-new-project` writes one combined JSON file per workflow run
- `create-new-project` filters both nested raw blocks to the matched station ids
- CLI and GUI continue to report artifact paths and summaries normally
- empty-result cases still produce the expected top-level wrapper shape

## Risks And Mitigations

- Reconstructing the nested blocks from `dataretrieval` means the output will be USGS-style rather than byte-for-byte raw.
  - Mitigation: keep the shape focused on the fields and nesting the downstream workflow cares about.
- The qualifying payload for bbox workflows may contain more rows than the final workflow result.
  - Mitigation: filter raw payload features to the matched station ids after current workflow intersection logic.

## Documentation Notes

- Update the package docs to explain that JSON artifacts are now combined USGS-style exports built from `dataretrieval`.
- Document the top-level wrapper keys and the workflow-specific second block names.
- Do not commit the spec or implementation artifacts automatically; the user requested no commits.

## Acceptance Criteria

- `add-data` writes one combined JSON artifact per run with `monitoring_locations` and `timeseries` `FeatureCollection` blocks.
- `create-new-project` writes one combined JSON artifact per workflow run with `monitoring_locations` and qualifying-data `FeatureCollection` blocks.
- Nested blocks remain `FeatureCollection` objects.
- CSV and parquet outputs still work.
- CLI and GUI continue to function with the new export contract.
