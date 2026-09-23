# CSV Import And Retry Robustness Design

## Context

Hydrologic Toolbox testing found that add-data downloads can succeed but then fail
when Hydrologic Toolbox imports the generated CSV. The clearest failing example is
discharge station `04193500` in HUC `04100009`: adding quotes around the station
name made Hydrologic Toolbox able to import and plot the discharge data.

The client also requested that HUC codes and station codes be treated as text.
They suggested `pandas.CategoricalDtype` because it can be faster than object
strings. That may be useful later for memory or performance, but it is not the
mechanism that controls CSV quoting. CSV quoting is controlled by the exporter.

`CategoricalDtype` changes how pandas stores repeated values internally. It does
not change the CSV writer's quoting policy. For example, a categorical value like
`MAUMEE RIVER AT WATERVILLE OH` still exports as:

```csv
MAUMEE RIVER AT WATERVILLE OH
```

not:

```csv
"MAUMEE RIVER AT WATERVILLE OH"
```

The same is true for station IDs and HUC codes. They can be categorical and still
write without quotes unless the CSV writer is explicitly told to quote them, or
unless the value contains a character that triggers automatic CSV quoting, such
as a comma, quote, or newline.

There is also a second reported issue where a leftover CSV from a previous failed
attempt can interfere with retrying the same download.

## Goal

Make add-data CSV files safer for Hydrologic Toolbox import by:

- consistently quoting identifier and descriptive header fields that must be read
  as text
- preserving HUC and station-like values as text in exported CSV metadata
- replacing existing CSV outputs safely on retry
- avoiding partial or stale output files from failed writes

Progress/status messaging is intentionally out of scope for this change and
should be handled as a follow-up.

## Non-Goals

- Do not redesign the add-data CSV schema.
- Do not change the shapefile export schema.
- Do not add progress bars or long-running status output in this change.
- Do not rely on `CategoricalDtype` as the CSV quoting fix.
- Do not change Hydrologic Toolbox behavior.

## Current Behavior

For `discharge` and `gw_daily`, the CSV has:

1. a commented metadata field-name line
2. a commented metadata value line
3. a reduced data table

The metadata value line currently forces quotes only for `Parameter` and
`Statistic`. Other text fields, including `Station name`, are quoted only if the
value contains a comma, quote, or newline.

For `gw_periodic`, the CSV has a modern metadata header block and body table.
`monitoring_location_name` is already force-quoted, but other identifier fields
still use default CSV quoting rules.

Output writing currently writes directly to the final CSV path.

## Proposed Design

### Header Text Quoting

Add a focused forced-quote policy for add-data CSV metadata value lines.

For reduced `discharge` and `gw_daily` CSV headers, force quote:

- `site_no`
- `Description`
- `Parameter`
- `Statistic`
- `Site number`
- `Station name`
- `HUC code`

Do not force quote numeric fields:

- `Latitude`
- `Longitude`
- `Drainage area`

For periodic CSV headers, force quote text identifier and code fields when they
are present:

- `monitoring_location_id`
- `monitoring_location_number`
- `monitoring_location_name`
- `site_type_code`
- `hydrologic_unit_code`
- `vertical_datum`
- `district_code`
- `state_code`
- `county_code`
- `country_code`
- `time_zone_abbreviation`
- `national_aquifer_code`
- `aquifer_code`
- `aquifer_type_code`
- `depth_source_code`

This keeps the files valid CSV while making Hydrologic Toolbox import behavior
more predictable for station names, station IDs, HUCs, and code-like values.

### Identifier Value Handling

Keep identifier values string-like at export time. The exporter should not coerce
station IDs, HUCs, or codes through numeric types. Empty values should continue to
export as empty CSV fields.

This can be done in the export formatting layer rather than mutating the source
DataFrames. If a later performance pass shows a measurable benefit from
`CategoricalDtype`, we can add it separately with benchmarks.

A focused characterization test should prove this assumption: converting station
IDs, HUC codes, and station names to `CategoricalDtype` does not force quotes in
`DataFrame.to_csv(...)`, while the export helper's `forced_quote_fields` does.

### Retry-Safe CSV Writing

Change time-series CSV writing to use an atomic replace pattern:

1. write the full CSV to a temporary sibling path
2. replace the final CSV path only after the write succeeds
3. remove the temporary file if writing fails

This means a failed export will not leave a half-written final CSV. A retry that
does call `waterdata_toolbox` will replace the existing final file with the new
successful output.

If Hydrologic Toolbox itself skips calling `waterdata_toolbox` because a stale
file already exists, that behavior will need to be addressed on the Hydrologic
Toolbox side. This change makes the `waterdata_toolbox` side idempotent when it
is invoked.

## Error Handling

- CSV formatting errors should still surface as normal command failures.
- Temporary files should be cleaned up on write failure when possible.
- Existing final files should not be deleted before a successful replacement is
  ready.

## Tests

Add focused offline coverage for:

- `CategoricalDtype` does not force pandas CSV quotes for station/HUC/name fields
- reduced discharge/daily header values force quote `Station name`, station IDs,
  HUC code, `Parameter`, and `Statistic`
- quoted station names work even when the station name has no comma
- periodic metadata values force quote station/HUC/code-like fields
- existing CSV files are replaced on successful retry
- failed temporary writes do not leave the temporary file behind

Keep live endpoint tests unchanged unless a live regression needs to be verified
manually.

## Validation

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -k 'not live' -q
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_xml_compat.py -v
```

Recommended manual smoke test after rebuilding the `.exe`:

```cmd
waterdata_toolbox_demo.exe add-data discharge --station-id 04193500 --output-dir C:\temp\wdt_test
```

Then confirm the generated `discharge_04193500.csv` imports into Hydrologic
Toolbox and that retrying the same command replaces the file cleanly.
