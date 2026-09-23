# Three-Call Add-Data Header And Rawer Shapefile Design

## Goal

Update the packaged CLI workflows so `add-data` uses three Water Data API calls for discharge and daily exports, allowing the CSV header to include both time-series metadata and monitoring-location metadata, while `create-new-project` moves closer to the raw Water Data monitoring-locations schema in its shapefile output.

## Approved Decisions

- `add-data` will use three Water Data API calls for discharge and daily workflows:
  - `daily` for row data
  - `time-series-metadata` for time-series header values
  - `monitoring-locations` for site header values
- The CSV header should include these site values:
  - `Site number`
  - `Station name`
  - `Latitude`
  - `Longitude`
  - `HUC code`
  - `Drainage area`
- The current time-series header values remain in scope:
  - `TS_ID`
  - `Parameter`
  - `Statistic`
  - `IV_TS_ID`
  - `Description`
- `create-new-project` should include all Water Data monitoring-location fields in the shapefile as far as the shapefile format allows.
- Water Data field names should be preserved as much as possible.
- Where a shapefile field name exceeds the format limit, use deterministic GDAL-style truncation:
  - keep the first 10 characters when unique
  - on collision, keep the first 8 characters and append `_1`, `_2`, and so on

## Why Three Calls Are Needed

The official Water Data API documentation splits the needed metadata across separate endpoints:

- `daily` provides row-level daily values plus identifiers such as `monitoring_location_id`, `parameter_code`, `statistic_id`, and `time_series_id`
- `time-series-metadata` provides `parent_time_series_id` and time-series description fields used by the legacy-style header
- `monitoring-locations` provides station attributes such as `monitoring_location_name`, latitude/longitude, `hydrologic_unit_code`, and `drainage_area`

There is no documented one-request join that returns all of those fields from a single `daily` request.

## Add-Data Design

### Workflows

- `discharge` and `gw_daily`
  - continue to use `daily` for the row data
  - add `time-series-metadata` for time-series header metadata
  - add `monitoring-locations` for site header metadata
- `gw_periodic`
  - keep the current `field-measurements` row retrieval
  - do not expand the scope of the new header behavior unless the same header contract is explicitly requested for periodic exports

### Header Contract

The CSV should keep the current custom layout with comment-prefixed metadata lines, but the metadata block should expand to include the requested site values from `monitoring-locations`.

The site values should come from raw Water Data fields with minimal transformation:

- `Site number` from `monitoring_location_number`
- `Station name` from `monitoring_location_name`
- `Latitude` from the location geometry or equivalent raw latitude field
- `Longitude` from the location geometry or equivalent raw longitude field
- `HUC code` from `hydrologic_unit_code`
- `Drainage area` from `drainage_area`

The time-series values should continue to come from the current API-derived fields:

- `TS_ID` from `time_series_id`
- `Parameter` from `parameter_code`
- `Statistic` from `statistic_id`
- `IV_TS_ID` from `parent_time_series_id`
- `Description` from the existing time-series description field used by the export

The row section should remain the reduced custom CSV body already approved for the app.

## Create-New-Project Shapefile Design

### Field Coverage

The shapefile export should stop curating a 10-field subset and instead attempt to include the full monitoring-locations attribute set returned by Water Data after filtering to the qualifying station IDs.

### Field Naming

Because shapefile `.dbf` field names are limited to 10 characters, exact raw names cannot always be preserved. The export should therefore:

- preserve raw Water Data names when they fit within 10 characters
- deterministically truncate longer names using the approved GDAL-style rule
- apply the same rule on every run so the same raw field always produces the same shapefile field name

### Data Values

Aside from shapefile-required compatibility handling, the export should avoid value-level renaming or curation. The goal is a fuller, rawer monitoring-locations attribute payload than the current reduced schema.

## Expected Code Areas

- `src/waterdata_toolbox_demo/timeseries.py`
  - add the third call and merge the header metadata
- `src/waterdata_toolbox_demo/exports.py`
  - expand the CSV header writer
  - replace the reduced station-schema mapping with full-field shapefile export plus deterministic truncation
- `src/waterdata_toolbox_demo/station_discovery.py`
  - keep the qualifying-station filtering
  - reduce only the normalization needed to support shapefile writing and geometry handling
- `tests/test_waterdata_toolbox_demo_package.py`
  - update CSV header expectations
  - update shapefile schema expectations
- `README.md` and package docs
  - document the three-call add-data behavior
  - document the fuller shapefile field behavior and truncation rule

## Risks

- Shapefile field-name collisions must be handled deterministically and tested carefully.
- Monitoring-location geometry and latitude/longitude values may require a tiny amount of compatibility handling depending on the exact frame shape returned by `dataretrieval`.
- The fuller shapefile schema may produce larger `.dbf` files and more awkward column names in GIS clients, but that tradeoff is intentional.
