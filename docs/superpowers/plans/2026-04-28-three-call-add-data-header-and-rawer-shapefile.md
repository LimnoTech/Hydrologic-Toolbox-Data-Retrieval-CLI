# Three-Call Add-Data Header And Rawer Shapefile Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `add-data` so discharge and daily CSV exports use three Water Data API calls and include both time-series and monitoring-location header metadata, while `create-new-project` writes shapefiles with the fuller monitoring-locations attribute set using deterministic GDAL-style field-name truncation where required.

**Architecture:** Keep the current CLI structure and retrieval split, but expand the `add-data` metadata assembly in `timeseries.py` to merge outputs from `daily`, `time-series-metadata`, and `monitoring-locations`. Replace the reduced 10-field shapefile export in `exports.py` with a dynamic shapefile schema builder that preserves raw monitoring-location columns as far as shapefile rules allow, and simplify `station_discovery.py` so the shapefile export starts from the filtered monitoring-locations frame rather than a curated app-level schema.

**Tech Stack:** Python, `dataretrieval.waterdata`, pandas, GeoPandas, pyshp, pytest

---

## File Map

- Modify: `src/waterdata_toolbox_demo/timeseries.py`
  - expand discharge/daily header retrieval from two calls to three
  - merge monitoring-location metadata into the CSV header payload
- Modify: `src/waterdata_toolbox_demo/exports.py`
  - expand the CSV header writer for the new site fields
  - replace the reduced shapefile schema with a dynamic raw-field export
  - add deterministic shapefile field-name truncation helpers
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
  - stop normalizing to the 10-field app schema
  - retain only the filtering and geometry compatibility needed for shapefile output
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
  - add regression tests for the three-call add-data header
  - update shapefile tests to expect fuller raw-field export and truncation behavior
- Modify: `README.md`
  - document the three-call `add-data` behavior and the fuller shapefile export
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
  - mirror the package-level behavior changes
- Modify: `docs/create-new-project-shapefile-fields.md`
  - replace the reduced-schema explanation with the new rawer-shapefile/truncation explanation

## Task 1: Lock The New CSV Header Contract With Failing Tests

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
- Reference: `src/waterdata_toolbox_demo/timeseries.py`
- Reference: `src/waterdata_toolbox_demo/exports.py`

- [ ] **Step 1: Add a failing add-data regression test for the three-call header**

Add a new test near the current `test_add_data_csv_only_artifacts` coverage that uses a `DummyWaterData` object with:

- `get_daily(...)`
- `get_time_series_metadata(...)`
- `get_monitoring_locations(...)`

The test should verify that the generated CSV header contains:

- `TS_ID`
- `Parameter`
- `Statistic`
- `IV_TS_ID`
- `Description`
- `Site number`
- `Station name`
- `Latitude`
- `Longitude`
- `HUC code`
- `Drainage area`

It should also verify that the site values come from the monitoring-locations payload and not from locally invented names.

- [ ] **Step 2: Add a failing assertion that discharge/daily add-data uses three retrieval calls**

Within the same test, collect simple call counters on the dummy methods and assert:

- one `get_daily(...)` call
- one `get_time_series_metadata(...)` call
- one `get_monitoring_locations(...)` call

Expected initial result: FAIL because the code does not yet call `get_monitoring_locations(...)` for the CSV header.

- [ ] **Step 3: Run the focused add-data tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "add_data_csv_only_artifacts or three_call" -v
```

Expected: the new test fails on missing header fields and/or missing monitoring-locations call.

- [ ] **Step 4: Commit the red test checkpoint**

```bash
git add tests/test_waterdata_toolbox_demo_package.py
git commit -m "Add add-data header regression coverage"
```

## Task 2: Lock The Rawer Shapefile Contract With Failing Tests

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
- Reference: `src/waterdata_toolbox_demo/exports.py`
- Reference: `src/waterdata_toolbox_demo/station_discovery.py`

- [ ] **Step 1: Replace the reduced-schema test with a fuller monitoring-locations export test**

Update the existing shapefile export test data so the input frame contains a wider set of raw Water Data fields such as:

- `monitoring_location_number`
- `monitoring_location_name`
- `hydrologic_unit_code`
- `drainage_area`
- `contributing_drainage_area`
- `time_zone_abbreviation`

Assert that the shapefile `.dbf` includes the corresponding fields, truncated only where required by the 10-character rule.

- [ ] **Step 2: Add a dedicated truncation-collision regression test**

Create a targeted test that passes two long raw column names whose first 10 characters would collide and assert the exported field names follow the approved rule:

- first unique name -> first 10 characters
- collision -> first 8 characters plus `_1`, `_2`, etc.

Expected examples should be concrete in the test so the algorithm is pinned down.

- [ ] **Step 3: Add a create-new-project integration test for full-field export**

Update the existing `run_create_new_project_section(...)` test so the dummy monitoring-locations frame includes raw Water Data columns beyond the old 10-field subset, and verify the resulting shapefile retains them in the exported `.dbf`.

- [ ] **Step 4: Run the focused shapefile tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "shapefile or create_project" -v
```

Expected: FAIL because the code still reduces the schema to the current curated field set.

- [ ] **Step 5: Commit the red shapefile test checkpoint**

```bash
git add tests/test_waterdata_toolbox_demo_package.py
git commit -m "Add raw-field shapefile regression coverage"
```

## Task 3: Implement The Three-Call Add-Data Header

**Files:**
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Add a helper that selects the monitoring-location row for the station**

In `timeseries.py`, add a small helper that:

- accepts a monitoring-locations frame
- matches the current `monitoring_location_id`
- returns the first matching row or `None`

Keep the fallback behavior explicit for empty frames.

- [ ] **Step 2: Expand the CSV header metadata builder**

Update the header-building logic so it accepts:

- the daily frame
- the time-series metadata frame
- the monitoring-locations frame

Build a single header mapping that includes:

- the existing time-series values
- the new site fields from raw monitoring-location data

Use raw API values where available, with only the minimum compatibility handling needed for empty values and coordinate extraction.

- [ ] **Step 3: Add the third Water Data call for discharge and daily workflows**

In `get_usgs_timeseries(...)`, after the `get_daily(...)` call and the existing `get_time_series_metadata(...)` call, add:

- `get_monitoring_locations(monitoring_location_id=...)`

Only do this for `discharge` and `gw_daily`, since that is the approved scope of the new header contract.

- [ ] **Step 4: Expand the CSV header writer**

In `exports.py`, update `_RAW_CSV_HEADER_FIELDS` and the metadata-row writer so the exported CSV header includes the six new site fields in the approved order.

Keep the body rows unchanged.

- [ ] **Step 5: Run the focused add-data tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "add_data_csv_only_artifacts or three_call" -v
```

Expected: PASS

- [ ] **Step 6: Commit the add-data implementation checkpoint**

```bash
git add src/waterdata_toolbox_demo/timeseries.py src/waterdata_toolbox_demo/exports.py tests/test_waterdata_toolbox_demo_package.py
git commit -m "Expand add-data header metadata"
```

## Task 4: Replace The Reduced Shapefile Schema With Fuller Raw-Field Export

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Remove the hard-coded reduced field mapping**

Delete or retire the code that depends on:

- `_STATION_SHAPEFILE_FIELDS`
- `_STATION_SHAPEFILE_FIELD_SPECS`
- `_reduce_station_shapefile_frame(...)`

Do not keep the reduced 10-field schema as the primary export path.

- [ ] **Step 2: Add deterministic raw-name truncation helpers**

In `exports.py`, add helpers that:

- accept the original raw column names
- preserve names of length `<= 10`
- truncate long names to the first 10 characters when unique
- apply the `8 chars + _1/_2/...` collision rule when needed

Keep the mapping deterministic and fully testable.

- [ ] **Step 3: Build DBF field specs dynamically from the raw frame**

Add a helper that inspects the filtered monitoring-locations frame and produces pyshp field specs dynamically, excluding only:

- geometry-bearing columns from the attribute table
- shapefile-incompatible helper columns that are not part of the raw monitoring-locations attributes

Prefer simple, conservative typing rules:

- strings/objects -> character fields
- integers/floats -> numeric fields
- booleans -> logical or character fields if needed for compatibility
- timestamps/dates -> character fields unless pyshp date support is intentionally added

- [ ] **Step 4: Update the shapefile row writer to use the dynamic schema**

Change `_write_station_shapefile(...)` so it:

- iterates over the dynamically generated truncated field list
- writes raw values under their truncated shapefile field names
- keeps geometry handling separate from attribute handling

- [ ] **Step 5: Simplify station discovery to keep raw monitoring-location columns**

In `station_discovery.py`, replace the current legacy-style normalization with a lighter-weight flow that:

- filters `candidate_frame` down to IDs also present in the qualifying frame
- preserves the raw monitoring-location columns
- ensures a GeoDataFrame with point geometry in `EPSG:4326`

Only keep compatibility logic that is strictly needed for geometry extraction or empty-frame behavior.

- [ ] **Step 6: Run the focused shapefile tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "shapefile or create_project" -v
```

Expected: PASS

- [ ] **Step 7: Commit the shapefile implementation checkpoint**

```bash
git add src/waterdata_toolbox_demo/exports.py src/waterdata_toolbox_demo/station_discovery.py tests/test_waterdata_toolbox_demo_package.py
git commit -m "Export fuller monitoring-location shapefiles"
```

## Task 5: Update Docs To Match The New Contracts

**Files:**
- Modify: `README.md`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `docs/create-new-project-shapefile-fields.md`

- [ ] **Step 1: Update the top-level README**

Document:

- `add-data` now uses three Water Data API calls for discharge/daily CSV header assembly
- `create-new-project` writes fuller monitoring-location shapefiles
- long raw field names may be truncated in the shapefile using the documented deterministic rule

- [ ] **Step 2: Update the package doc**

Mirror the same behavior changes in `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`.

- [ ] **Step 3: Rewrite the shapefile field note**

Update `docs/create-new-project-shapefile-fields.md` so it no longer describes a reduced 10-field schema. Replace it with:

- why raw Water Data fields are now preserved more fully
- why exact names still cannot always survive in a shapefile
- the deterministic truncation rule used by the export

- [ ] **Step 4: Run the docs-facing test coverage**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "package_build_docs" -v
```

Expected: PASS

- [ ] **Step 5: Commit the doc updates**

```bash
git add README.md src/waterdata_toolbox_demo/waterdata-package-cli-gui.md docs/create-new-project-shapefile-fields.md tests/test_waterdata_toolbox_demo_package.py
git commit -m "Document three-call headers and shapefile truncation"
```

## Task 6: Full Verification And Smoke Checks

**Files:**
- Modify: none
- Verify: `tests/test_waterdata_toolbox_demo_package.py`
- Verify: runtime outputs under `dist/outputs/`

- [ ] **Step 1: Run the full package test file**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -v
```

Expected: all tests PASS.

- [ ] **Step 2: Run a create-new-project smoke test**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --output-dir dist/outputs/three_call_shape_smoke
```

Expected:

- `dist/outputs/three_call_shape_smoke/discharge.shp`
- matching `.shx`, `.dbf`, `.prj`, `.cpg`
- `.dbf` contains a fuller set of monitoring-location attributes than the old reduced schema

- [ ] **Step 3: Run an add-data smoke test**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo add-data --discharge --station-id 02225500 --parameter-code 00060 --output-dir dist/outputs/three_call_csv_smoke
```

Expected:

- `dist/outputs/three_call_csv_smoke/discharge_02225500.csv`
- header includes both the time-series metadata fields and the six site metadata fields

- [ ] **Step 4: Inspect the generated CSV and shapefile metadata manually**

Check that:

- the CSV header values match the Water Data responses
- the shapefile field names follow the documented truncation rule
- no reduced legacy 10-field schema remains in the create-project output

- [ ] **Step 5: Commit the verification checkpoint if requested**

```bash
git add README.md pyproject.toml src/waterdata_toolbox_demo/*.py tests/test_waterdata_toolbox_demo_package.py docs/create-new-project-shapefile-fields.md
git commit -m "Finalize three-call headers and rawer shapefile export"
```
