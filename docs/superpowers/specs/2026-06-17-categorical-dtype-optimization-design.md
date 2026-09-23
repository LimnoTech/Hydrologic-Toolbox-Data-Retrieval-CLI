# Categorical Dtype Optimization Design

## Summary

Add targeted `pandas.CategoricalDtype` conversion for repeated Water Data string/code fields so large in-memory frames use less memory before export and payload return.

## Context

The CSV quote issue was solved in the export layer by explicitly forcing selected CSV fields to be quoted. `pandas.CategoricalDtype` is separate from that behavior: it preserves values while storing repeated categorical values more efficiently than plain object/string columns.

## Goals

- Convert repeated identifier/code/text columns to pandas `category` dtype on frames returned by the station-discovery and time-series workflows.
- Keep CSV formatting and forced-quote behavior unchanged.
- Avoid broad auto-detection that might unexpectedly convert arbitrary free-text fields.
- Keep the implementation small and easy to test.

## Non-Goals

- Do not use categorical dtype as a CSV quoting mechanism.
- Do not change CLI signatures, output file names, shapefile schema, XML compatibility behavior, or live endpoint arguments.
- Do not convert geometry or numeric measurement columns.

## Design

Create a small shared helper module with:

- A function that takes a frame and a list of column names.
- The function converts only existing columns.
- The function skips columns that are already categorical.
- The function returns a frame, so call sites can use it fluently.

Apply the helper in two places:

- `timeseries.get_usgs_timeseries()` after `station_id` and `workflow_type` are added, before records are created and CSV export runs.
- `station_discovery._normalize_station_frame()` after filtering, deduping, and sorting, before the frame is converted to a GeoDataFrame and shapefile export runs.

## Target Columns

Time-series candidates:

- `monitoring_location_id`
- `monitoring_location_number`
- `time_series_id`
- `parent_time_series_id`
- `parameter_code`
- `statistic_id`
- `approval_status`
- `qualifier`
- `station_id`
- `workflow_type`
- `vertical_datum`
- `measuring_agency`

Station-discovery candidates:

- `agency_code`
- `monitoring_location_id`
- `monitoring_location_number`
- `monitoring_location_name`
- `site_type_code`
- `horizontal_position_method_code`
- `original_horizontal_datum`
- `district_code`
- `state_code`
- `county_code`
- `country_code`
- `hydrologic_unit_code`
- `basin_code`
- `time_zone_abbreviation`
- `national_aquifer_code`
- `aquifer_code`
- `aquifer_type_code`
- `depth_source_code`

## Testing

Add focused tests that prove:

- The shared helper converts only existing target columns to categorical dtype.
- `get_usgs_timeseries()` returns a frame with expected categorical columns.
- Station discovery returns a GeoDataFrame with expected categorical columns.
- Existing CSV quote tests continue passing.

## Risks

Categorical dtype can affect downstream dtype inspection. The workflows currently serialize/export values and do not rely on object dtype specifically, so this is low risk. The change is intentionally targeted and avoids numeric, datetime, and geometry fields.
