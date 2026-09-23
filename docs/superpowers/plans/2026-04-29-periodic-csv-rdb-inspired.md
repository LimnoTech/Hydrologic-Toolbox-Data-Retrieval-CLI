# Periodic CSV RDB-Inspired Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `gw_periodic` `add-data` export a custom RDB-inspired `.csv` with a commented metadata block and a deliberate measurement table built only from modern Water Data API fields.

**Architecture:** Extend the periodic `add-data` path to fetch monitoring-location metadata alongside field measurements, build structured periodic header metadata in `timeseries.py`, and route periodic exports through a dedicated custom CSV writer in `exports.py`. Follow the same broad pattern as discharge/daily, but use a richer periodic header block and exclude app-added demo columns from the periodic body.

**Tech Stack:** Python, argparse, pandas, dataretrieval.waterdata, csv, pathlib, pytest

---

### File Map

**Modify:**
- `src/waterdata_toolbox_demo/timeseries.py`
  - Add periodic monitoring-location fetch
  - Build periodic header metadata from modern Water Data fields
  - Stop treating periodic as a plain raw dump path
- `src/waterdata_toolbox_demo/exports.py`
  - Add periodic-specific metadata field ordering
  - Add periodic body-frame preparation that excludes app-added demo columns
  - Add periodic custom CSV writer path
- `README.md`
  - Update periodic output description to reflect the new header-plus-table behavior

**Create or restore tests as needed:**
- `tests/test_periodic_csv_format.py`
  - Focused tests for periodic header/body export behavior

### Task 1: Add a periodic export contract test

**Files:**
- Create: `tests/test_periodic_csv_format.py`
- Reference: `src/waterdata_toolbox_demo/exports.py`
- Reference: `src/waterdata_toolbox_demo/timeseries.py`

- [ ] **Step 1: Write a failing export-format test**

Create a test that:
- builds a small fake periodic frame with realistic `field-measurements` columns
- includes app-added columns `station_id` and `workflow_type`
- supplies a periodic metadata dictionary built from modern Water Data names
- calls the periodic CSV export path
- asserts:
  - the file starts with commented header lines
  - the body table exists
  - `station_id` is not in the body header
  - `workflow_type` is not in the body header
  - `time` and `value` are in the body header

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
python -m pytest tests/test_periodic_csv_format.py -v
```

Expected:
- fail because periodic still uses the plain `frame.to_csv(...)` fallback

- [ ] **Step 3: Add one more failing test for header field selection**

Add a second test that verifies the periodic header only includes fields present in the provided metadata and does not invent legacy-only fields.

- [ ] **Step 4: Run both tests to confirm failure**

Run:

```bash
python -m pytest tests/test_periodic_csv_format.py -v
```

Expected:
- both fail against current behavior

### Task 2: Build periodic header metadata in `timeseries.py`

**Files:**
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Test: `tests/test_periodic_csv_format.py`

- [ ] **Step 1: Add a helper for periodic header metadata**

Add a focused helper that accepts:
- the periodic measurement frame
- the monitoring-locations frame

It should build a metadata dictionary using only modern Water Data names and only values present in the source frames.

Include fields in a stable order matching the spec direction, such as:
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

- [ ] **Step 2: Fetch monitoring-location metadata for periodic**

Update `get_usgs_timeseries(...)` so `gw_periodic` also calls:

```python
waterdata_module.get_monitoring_locations(
    monitoring_location_id=monitoring_location_id,
)
```

Do this in the same shape already used by discharge/daily where practical.

- [ ] **Step 3: Build `csv_header_metadata` for periodic**

Set periodic `csv_header_metadata` from the new helper instead of leaving it `None`.

- [ ] **Step 4: Run the focused tests**

Run:

```bash
python -m pytest tests/test_periodic_csv_format.py -v
```

Expected:
- tests still fail at the export formatting layer, but now periodic metadata exists

### Task 3: Add a periodic-specific CSV writer path

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Test: `tests/test_periodic_csv_format.py`

- [ ] **Step 1: Add periodic header field ordering**

Define a periodic metadata field order constant for the commented header block using modern Water Data names.

- [ ] **Step 2: Add a periodic body-frame preparation helper**

Create a helper that:
- starts from the periodic frame
- drops app-added columns:
  - `station_id`
  - `workflow_type`
- keeps only real API-provided fields
- preserves measurement-table usefulness, prioritizing:
  - `monitoring_location_id`
  - `time`
  - `value`
  - `vertical_datum`
  - `approval_status`
  - `qualifier`
  - `measuring_agency`
  - `parameter_code`

If other API-provided columns are present and useful, keep them after those core fields.

- [ ] **Step 3: Add a periodic CSV writer helper**

Implement a dedicated helper that writes:
- one or more commented metadata lines at the top
- then the periodic body table underneath via `csv.writer`

Use the same CSV escaping conventions already established in this file instead of inventing a separate writer style.

- [ ] **Step 4: Route periodic through the custom path**

Update `_write_timeseries_csv_artifact(...)` so it distinguishes:
- discharge/daily reduced-header CSV path
- periodic custom RDB-inspired CSV path
- plain fallback only when no custom export contract applies

- [ ] **Step 5: Run the focused periodic tests**

Run:

```bash
python -m pytest tests/test_periodic_csv_format.py -v
```

Expected:
- pass

### Task 4: Add an integration-style timeseries test

**Files:**
- Create or extend: `tests/test_periodic_csv_format.py`
- Modify if needed: `src/waterdata_toolbox_demo/timeseries.py`

- [ ] **Step 1: Write a test around `get_usgs_timeseries(...)` for `gw_periodic`**

Use a stub `waterdata_module` object with:
- `get_field_measurements(...)`
- `get_monitoring_locations(...)`

Assert that:
- periodic now fetches monitoring-location metadata
- returned `files` include the periodic CSV
- the written file contains commented header lines plus a table body

- [ ] **Step 2: Run just the integration-style test**

Run:

```bash
python -m pytest tests/test_periodic_csv_format.py -k "get_usgs_timeseries or integration" -v
```

Expected:
- pass

### Task 5: Update product docs

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the periodic command description**

Revise the periodic row in the README command table so it no longer reads like a plain raw CSV dump.

- [ ] **Step 2: Add a short note about periodic formatting**

Add one concise note explaining that:
- periodic stays `.csv`
- periodic now uses a commented metadata header plus a measurement table
- the layout is inspired by the old groundwater RDB style but uses modern Water Data names and values

- [ ] **Step 3: Review README examples for consistency**

Confirm the README examples still match the active CLI shape:
- `create-new-project --wf ...`
- `add-data <workflow> --station-id ...`

### Task 6: Full verification

**Files:**
- Verify modified source and test files

- [ ] **Step 1: Run the focused periodic tests**

Run:

```bash
python -m pytest tests/test_periodic_csv_format.py -v
```

Expected:
- pass

- [ ] **Step 2: Run the broader CLI-local test suite if available**

Run:

```bash
python -m pytest tests -v
```

Expected:
- pass, or clearly identify any pre-existing/local-only test-surface issues

- [ ] **Step 3: Run one live periodic CLI command if network is available**

Run:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo add-data periodic --station-id 410947071344803 --output-dir dist/outputs/add_data_periodic
```

Expected:
- periodic CSV is written
- file begins with commented metadata lines
- body table does not include `station_id` or `workflow_type`

- [ ] **Step 4: Manually inspect the output**

Confirm the resulting periodic file:
- stays `.csv`
- uses modern Water Data names in the metadata block
- includes a deliberate measurement table
- looks structurally closer to the old groundwater RDB layout than the current plain CSV
