# Periodic CSV RDB-Inspired Design

## Summary

Update the `gw_periodic` `add-data` export so it no longer writes a plain raw CSV dump. Keep the output as `.csv`, but format it more like the approved discharge and daily exports: a metadata header block first, then a table underneath.

The periodic export should be modeled after the legacy NWIS groundwater-levels RDB layout in spirit, while using:
- modern Water Data API field names
- modern Water Data API values
- only fields already returned by the relevant API calls

## Goals

- Keep periodic output as `.csv`
- Replicate the old groundwater file layout style as much as possible
- Use real fields from the new Water Data API only
- Avoid app-added demo columns in the periodic body table
- Make the periodic export feel consistent with the current discharge and daily CSV outputs

## Non-Goals

- Do not change the periodic output to `.rdb`
- Do not invent or synthesize legacy fields that the new API does not provide
- Do not include app-only convenience fields like `station_id` or `workflow_type` in the periodic CSV unless the API itself provides them
- Do not force old NWIS field names into the periodic CSV header or body

## Data Sources

The periodic export should use:

1. `get_field_measurements(...)`
- source of periodic groundwater measurement rows
- source of the body-table data

2. `get_monitoring_locations(...)`
- source of site-level metadata for the header block

## Export Shape

The periodic export remains a `.csv` file with two major sections:

1. Commented metadata header block
2. CSV table body

This mirrors the established pattern already used for discharge and daily:
- top-of-file commented header lines
- normal delimited table underneath

## Header Block

The periodic header should be richer than the current discharge/daily two-line header because the old groundwater file carries more site context.

The header block should include as many of these modern Water Data fields as are available from the new API response:

- `monitoring_location_id`
- `monitoring_location_name`
- `site_type_code`
- `geometry`
- `hydrologic_unit_code`
- `altitude`
- `altitude_method_code`
- `altitude_accuracy`
- `vertical_datum`
- `district_code`
- `state_code`
- `county_code`
- `country_code`
- `time_zone_abbreviation`
- `uses_daylight_savings`
- `construction_date`
- `drainage_area`
- `contributing_drainage_area`
- `national_aquifer_code`
- `aquifer_code`
- `aquifer_type_code`
- `well_constructed_depth`
- `hole_constructed_depth`
- `depth_source_code`

The header should not rename these to legacy NWIS names. The periodic file should use modern Water Data naming and values, just with a legacy-inspired layout.

## Body Table

The body table should stop being a raw full-frame dump and instead become a deliberate periodic measurement table built from `field-measurements`.

The body should include only fields already returned by the periodic API call and should aim to replicate the old groundwater-timeseries section as much as possible with modern names.

Expected body fields, when present:

- `monitoring_location_id`
- `time`
- `value`
- `vertical_datum`
- `approval_status`
- `qualifier`
- `measuring_agency`
- `parameter_code`

If other useful periodic measurement fields are already present in the API result, they may be included, but only if they are true API fields and not app-added columns.

## Excluded Columns

The periodic CSV body should exclude app-added demo columns from the current workflow:

- `station_id`
- `workflow_type`

More generally, any column created only by the application for internal/demo convenience should be excluded unless it is directly provided by the source API response.

## Formatting Principles

- Keep the file as UTF-8 CSV
- Keep the header block commented, like the approved discharge/daily format
- Use a predictable, readable field order
- Prefer omission over invention when a legacy field has no modern equivalent

## Known Limits

The modern Water Data API does not provide a perfect one-to-one replacement for every part of the old groundwater RDB file. This means:

- the code-reference sections from the old RDB are out of scope
- period-of-record summary blocks are out of scope unless already available from the new calls
- legacy-only fields with no modern equivalent should be omitted

The goal is to replicate the old layout style and usefulness, not to fabricate an exact legacy RDB clone.

## Implementation Direction

Implementation should follow the same broad pattern already used by discharge and daily:

- gather header metadata in `timeseries.py`
- pass structured periodic header metadata into the export layer
- write the periodic CSV with a dedicated custom path in `exports.py`

The periodic export should no longer fall back to the plain `frame.to_csv(...)` path once this work is complete.
