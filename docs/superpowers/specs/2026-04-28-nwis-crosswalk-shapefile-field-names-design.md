# NWIS Crosswalk Shapefile Field Names Design

## Summary

`create-new-project` shapefiles should stop using raw Water Data field names plus `_1`, `_2`, and other collision suffixes. Instead, the shapefile attribute schema should be driven by a code-local NWIS/Water Data crosswalk: map each fetched Water Data field to its legacy NWIS name, then truncate that legacy NWIS name to 10 characters for the DBF field name. This keeps the field names familiar to NWIS users, avoids ambiguous collision suffixes, and lets us delete the generic duplicate-name truncation path.

## Goals

- Replace the current raw-name collision logic with a deterministic NWIS-style crosswalk.
- Use only fields we actually fetch and intend to export.
- Omit unavailable legacy fields from the DBF attribute table.
- Keep `dec_lat_va` and `dec_long_va` in the DBF as legacy coordinate attributes derived from fetched geometry.
- Keep geometry in the shapefile geometry itself.
- Remove now-irrelevant code, tests, and docs tied to raw-name suffix handling.

## Non-Goals

- Recreating every historical NWIS `/site` field.
- Writing a separate crosswalk file next to the shapefile.
- Changing the three-call `add-data` CSV header design.

## Current Problem

The current shapefile writer preserves raw monitoring-location column names and truncates them directly to fit shapefile DBF limits. When two long names collide, the exporter falls back to suffixes like `_1` and `_2`. That behavior is deterministic, but it is not easy to read, and it forces users to infer or document which raw field ended up behind names like `monitori_1`.

## Proposed Design

### Field-name rule

For each monitoring-location field we choose to export:

1. Start with the Water Data field name.
2. Convert it to the legacy NWIS `/site` field name using a code-local crosswalk.
3. Truncate the resulting NWIS field name to 10 characters for the shapefile DBF field name.
4. Validate that the final 10-character names are unique.

If a crosswalked field would still collide after truncation, the export should fail with a clear error rather than generating `_1`, `_2`, or other fallback names.

### Exported field scope

The shapefile should only include fields that:

- are returned by the monitoring-locations call,
- have a meaningful NWIS crosswalk target,
- and are intended to be part of the attribute table.

Entries marked `No longer provided.` are not exported. Entries represented by shapefile geometry rather than attributes are also not exported as DBF fields.
The exception is the legacy coordinate pair `dec_lat_va` and `dec_long_va`, which should be derived from the fetched point geometry and retained in the DBF for compatibility.

### Crosswalk-driven attribute schema

The code-local crosswalk should cover the fetched monitoring-location values we intend to keep:

| Water Data field | NWIS-style name | Shapefile field |
| --- | --- | --- |
| `agency_code` | `agency_cd` | `agency_cd` |
| `monitoring_location_number` | `site_no` | `site_no` |
| `monitoring_location_name` | `station_nm` | `station_nm` |
| `site_type_code` | `site_tp_cd` | `site_tp_cd` |
| `geometry` | `dec_lat_va` | `dec_lat_va` |
| `geometry` | `dec_long_va` | `dec_long_v` |
| `horizontal_position_method_code` | `coord_meth_cd` | `coord_meth_` |
| `horizontal_positional_accuracy` | `coord_acy_cd` | `coord_acy_` |
| `original_horizontal_datum` | `coord_datum_cd` | `coord_datu` |
| `district_code` | `district_cd` | `district_c` |
| `state_code` | `state_cd` | `state_cd` |
| `county_code` | `county_cd` | `county_cd` |
| `country_code` | `country_cd` | `country_cd` |
| `altitude` | `alt_va` | `alt_va` |
| `altitude_method_code` | `alt_meth_cd` | `alt_meth_c` |
| `altitude_accuracy` | `alt_acy_va` | `alt_acy_va` |
| `vertical_datum` | `alt_datum_cd` | `alt_datum_` |
| `hydrologic_unit_code` | `huc_cd` | `huc_cd` |
| `basin_code` | `basin_cd` | `basin_cd` |
| `construction_date` | `construction_dt` | `constructi` |
| `drainage_area` | `drain_area_va` | `drain_area` |
| `contributing_drainage_area` | `contrib_drain_area_va` | `contrib_dr` |
| `time_zone_abbreviation` | `tz_cd` | `tz_cd` |
| `uses_daylight_savings` | `local_time_fg` | `local_time` |
| `national_aquifer_code` | `nat_aqfr_cd` | `nat_aqfr_` |
| `aquifer_code` | `aqfr_cd` | `aqfr_cd` |
| `aquifer_type_code` | `aqfr_type_cd` | `aqfr_type_` |
| `well_constructed_depth` | `well_depth_va` | `well_depth` |
| `hole_constructed_depth` | `hole_depth_va` | `hole_depth` |
| `depth_source_code` | `depth_src_cd` | `depth_src_` |

### Omitted fields

The following categories should be omitted from the shapefile DBF:

- legacy fields marked `No longer provided.`
- monitoring-location fields that do not participate in this NWIS-style crosswalk

Geometry remains in the `.shp` feature geometry and `.prj` sidecar. For compatibility, its decimal coordinates should also be written into `dec_lat_va` and `dec_long_va` DBF columns.

## Code Changes

### `exports.py`

- Replace the raw-column truncation logic with a code-local crosswalk constant.
- Replace the generic `_truncate_shapefile_field_names(...)` path with:
  - Water Data field allowlist selection,
  - Water Data -> NWIS alias mapping,
  - geometry -> `dec_lat_va` / `dec_long_va` derivation,
  - 10-character truncation of those NWIS aliases,
  - uniqueness validation.
- Keep DBF type inference and DBF-safe value conversion.
- Remove code that exists only to support raw-name collision suffixes.

### `station_discovery.py`

- Keep filtering to qualifying monitoring locations.
- Ensure the resulting frame contains the Water Data fields referenced by the crosswalk.
- Remove normalization behavior that only existed to support the old ad hoc naming path.

### Tests

Update tests so they assert:

- exported shapefile fields use the NWIS-style names after 10-character truncation,
- no `_1` / `_2` duplicate suffix behavior remains,
- omitted legacy/unavailable fields do not appear,
- DBF-safe type conversion still works,
- geometry is still written correctly.

### Docs

Update docs to describe:

- why the shapefile schema uses NWIS-style field names,
- why only crosswalked fetched fields are exported,
- why some legacy names are omitted while `dec_lat_va` / `dec_long_va` are retained,
- and that the duplicate-suffix behavior has been removed.

## Error Handling

- If a required crosswalked Water Data field is missing from the fetched frame, fail with a clear export error.
- If point geometry is missing when `dec_lat_va` / `dec_long_va` need to be derived, fail with a clear export error.
- If two mapped NWIS names still collide after 10-character truncation, fail with a clear export error naming both source fields.
- If geometry is missing or invalid, keep the existing explicit shapefile export error behavior.

## Testing Strategy

- Unit-test the crosswalk mapping and final 10-character field names.
- Unit-test geometry-to-`dec_lat_va` / `dec_long_va` derivation.
- Unit-test collision detection on the truncated NWIS aliases.
- Regression-test shapefile export with a representative monitoring-location frame.
- Regression-test that the old raw-name suffix logic is no longer reachable.

## Acceptance Criteria

- `create-new-project` shapefiles no longer contain raw Water Data field names like `monitoring...` or collision suffixes like `_1`.
- Exported DBF fields use NWIS-style names derived from the code-local crosswalk and truncated to 10 characters.
- Only fields we actually fetch and explicitly crosswalk are included.
- Legacy fields marked unavailable are omitted, while `dec_lat_va` and `dec_long_va` are retained from geometry.
- The exporter still writes valid shapefiles with consistent DBF values and point geometry.

## Notes

This design intentionally replaces the earlier “raw monitoring-location fields with little manipulation” direction for shapefile field names. The values still come from Water Data, but the shapefile schema becomes a controlled NWIS-style compatibility layer so the output is more readable and predictable in GIS tools.
