# Issue: Expand Add-Data Headers And Rawer Create-New-Project Shapefiles

## Summary

Update the packaged CLI workflows so `add-data` includes both time-series metadata and site metadata in the CSV header, and `create-new-project` writes shapefiles with a fuller set of raw Water Data monitoring-location fields.

## Background

The current `add-data` export is centered on daily-value output and only includes part of the metadata we want in the CSV header. The current `create-new-project` shapefile export also reduces the monitoring-location schema down to a small curated field set, which limits how much of the Water Data payload makes it into the project artifact. We want to keep the current CLI structure, but move closer to the raw Water Data model where practical.

## Objectives

- Use three Water Data API calls for `add-data` discharge and daily workflows:
  - `daily`
  - `time-series-metadata`
  - `monitoring-locations`
- Keep the existing time-series header values in the CSV:
  - `TS_ID`
  - `Parameter`
  - `Statistic`
  - `IV_TS_ID`
  - `Description`
- Add the following site metadata to the CSV header:
  - `Site number`
  - `Station name`
  - `Latitude`
  - `Longitude`
  - `HUC code`
  - `Drainage area`
- Keep the approved reduced CSV row section for the time-series body.
- Change `create-new-project` shapefile export so it includes the fuller monitoring-location attribute set instead of the current reduced 10-field schema.
- Preserve raw Water Data field names where possible.
- When shapefile field-name limits require shortening, use deterministic GDAL-style truncation.

## Acceptance Criteria

- `add-data --discharge` and `add-data --daily` make three Water Data calls and write a CSV whose header includes both the time-series metadata and the requested site metadata.
- `create-new-project` shapefiles contain a broader set of monitoring-location attributes than the current reduced schema.
- Long shapefile field names are truncated consistently and predictably.
- The current CLI command structure remains in place.
- Tests cover the expanded CSV header behavior and the fuller shapefile field behavior.
- README/package docs are updated to describe the new contracts.

## Out Of Scope

- Reintroducing GUI-first runtime behavior
- Returning to JSON/parquet artifact output for the packaged app
- Replacing shapefile output with GeoJSON for `create-new-project`
- Changing the approved reduced CSV body layout for the time-series rows

## Notes

- A shapefile cannot preserve every raw Water Data field name exactly because the `.dbf` attribute table limits field names to 10 characters.
- The site metadata requested for the CSV header is not all available from the `daily` endpoint alone, which is why the header needs the extra `time-series-metadata` and `monitoring-locations` calls.
