# Categorical Dtype Optimization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert repeated Water Data string/code columns to `pandas.CategoricalDtype` in station-discovery and time-series frames without changing CSV output formatting.

**Architecture:** Add one shared frame helper module and call it from the two frame-producing workflow paths. Keep export-layer CSV quote rules independent from dtype optimization.

**Tech Stack:** Python, pandas, GeoPandas-compatible frames, pytest.

---

### Task 1: Add Shared Categorical Helper

**Files:**
- Create: `src/waterdata_toolbox_demo/frame_types.py`
- Test: `tests/test_frame_types.py`

- [ ] **Step 1: Write the failing helper tests**

Create tests that assert existing target columns become `category`, missing target columns are ignored, non-target columns are unchanged, and already-categorical columns remain categorical.

- [ ] **Step 2: Run helper tests to verify they fail**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_frame_types.py -v`

Expected: FAIL because `waterdata_toolbox_demo.frame_types` does not exist yet.

- [ ] **Step 3: Implement the helper**

Add `categorize_existing_columns(frame, column_names)` using `pd.CategoricalDtype()` and `astype()`.

- [ ] **Step 4: Run helper tests to verify they pass**

Run the same pytest command.

Expected: PASS.

### Task 2: Apply Categoricals To Time-Series Frames

**Files:**
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Test: `tests/test_frame_types.py`

- [ ] **Step 1: Write the failing time-series integration test**

Use a fake waterdata module to call `get_usgs_timeseries()` and assert returned repeated columns such as `parameter_code`, `approval_status`, `station_id`, and `workflow_type` are categorical.

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_frame_types.py -v`

Expected: FAIL because `get_usgs_timeseries()` does not apply categoricals yet.

- [ ] **Step 3: Apply the helper in `get_usgs_timeseries()`**

After `station_id` and `workflow_type` columns are added, call `categorize_existing_columns()` with the time-series target column list.

- [ ] **Step 4: Run the test to verify it passes**

Run the same pytest command.

Expected: PASS.

### Task 3: Apply Categoricals To Station-Discovery Frames

**Files:**
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Test: `tests/test_frame_types.py`

- [ ] **Step 1: Write the failing station-discovery integration test**

Patch GeoPandas loading with a lightweight fake so `_normalize_station_frame()` can run without writing shapefiles, then assert station code/name fields are categorical on the returned frame.

- [ ] **Step 2: Run the test to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_frame_types.py -v`

Expected: FAIL because `_normalize_station_frame()` does not apply categoricals yet.

- [ ] **Step 3: Apply the helper in `_normalize_station_frame()`**

After filtering, deduping, sorting, and resetting the index, call `categorize_existing_columns()` with the station-discovery target column list.

- [ ] **Step 4: Run the test to verify it passes**

Run the same pytest command.

Expected: PASS.

### Task 4: Regression Verification

**Files:**
- Existing tests only.

- [ ] **Step 1: Run categorical tests**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_frame_types.py -v`

Expected: PASS.

- [ ] **Step 2: Run CSV quote tests**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_csv_export_assumptions.py -v`

Expected: PASS, proving categorical dtype remains separate from quote formatting.

- [ ] **Step 3: Run non-live CLI signature tests**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -k 'not live' -q`

Expected: PASS.
