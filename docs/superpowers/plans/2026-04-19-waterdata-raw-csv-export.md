# WaterData Raw CSV Export Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change add-data CSV exports so the CLI and GUI both write a metadata-preamble CSV with raw API header fields and a reduced four-column daily-values body.

**Architecture:** Keep `get_usgs_timeseries(...)` as the shared add-data entry point, add one time-series metadata lookup there, and move CSV formatting into focused helpers in `exports.py`. JSON and parquet stay on their current paths while the CSV path becomes a custom writer that consumes resolved header metadata plus a reduced body frame.

**Tech Stack:** Python, dataretrieval, pandas, pytest, tkinter

---

## File Map

- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

### Task 1: Add failing tests for the new CSV contract

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write a failing CSV export helper test**

Add a test that calls `export_timeseries_artifacts(...)`, reads the CSV output, and asserts:
- line 1 is `# TS_ID,Parameter,Statistic,IV_TS_ID,Description,site_no`
- line 2 contains the expected raw API-derived values
- line 3 is `Daily values,Time,Approval status,Qualifier`

- [ ] **Step 2: Write a failing add-data integration test**

Add a test that stubs `get_daily(...)`, `get_time_series_metadata(...)`, and `get_monitoring_locations(...)`, runs `get_usgs_timeseries(...)`, and asserts the CSV body only contains:
- `Daily values`
- `Time`
- `Approval status`
- `Qualifier`

- [ ] **Step 3: Run the focused tests to verify they fail**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "raw_csv or csv_contract or timeseries_csv" -v`
Expected: FAIL because the current code still writes a plain DataFrame CSV without the metadata preamble.

### Task 2: Add CSV formatting helpers in `exports.py`

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Implement the minimal CSV helper surface**

Add helpers that:
- reduce a DataFrame to `value`, `time`, `approval_status`, and `qualifier`
- rename those columns to `Daily values`, `Time`, `Approval status`, and `Qualifier`
- write the two `#` metadata lines plus the reduced body table

- [ ] **Step 2: Re-run the focused helper tests**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "raw_csv or csv_contract" -v`
Expected: PASS

### Task 3: Add metadata lookup and row-resolution logic in `timeseries.py`

**Files:**
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Implement the failing-series-match test if needed**

Add or extend a test so metadata row selection prefers the row whose `time_series_id` matches the daily frame.

- [ ] **Step 2: Implement the minimal metadata integration**

Update `get_usgs_timeseries(...)` to:
- call `get_time_series_metadata(...)` for daily workflows
- choose the matching metadata row
- build a header metadata mapping with raw API values
- pass that metadata into the CSV export helper

- [ ] **Step 3: Re-run the timeseries-focused tests**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "timeseries_csv or station_id_normalization or add_data_combined_json" -v`
Expected: PASS

### Task 4: Update docs for the new CSV shape

**Files:**
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`

- [ ] **Step 1: Document the add-data CSV contract**

Describe that add-data CSV exports now:
- begin with raw API metadata header lines
- use `site_no = monitoring_location_id`
- reduce the body to the four requested columns

### Task 5: Run the relevant regression slice

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Run the targeted regression suite**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "export_timeseries_artifacts or raw_csv or timeseries or cli_add_data or gui_add_data or docs_cover_package" -v`
Expected: PASS

- [ ] **Step 2: Inspect generated CSV output manually if needed**

Verify that a representative discharge CSV begins with the expected two `#` lines and the reduced body header.

- [ ] **Step 3: Leave git uncommitted**

Do not create commits or stage files unless the user asks later.
