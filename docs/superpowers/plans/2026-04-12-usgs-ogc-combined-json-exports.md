# USGS OGC Combined JSON Exports Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the CLI and GUI workflows so their JSON artifacts become combined USGS-style `FeatureCollection` payloads built from `dataretrieval` results while keeping CSV and parquet export behavior intact.

**Architecture:** Keep the current `dataretrieval` and DataFrame workflow logic for app behavior, and update export helpers so JSON artifacts are written from combined `FeatureCollection` payloads reconstructed from those frames instead of flattened records. The workflow modules remain the place where filtering and output naming decisions live.

**Tech Stack:** Python, requests or urllib-compatible HTTP access, dataretrieval, pandas, GeoPandas, pytest, tkinter

---

## File Map

- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Modify: `src/waterdata_toolbox_demo/cli.py`
- Modify: `src/waterdata_toolbox_demo/gui.py`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

### Task 1: Add focused failing tests for the new JSON contract

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing add-data JSON export test**

Add a test that stubs the workflow dependencies, runs `get_usgs_timeseries(...)`, reads the emitted JSON file, and asserts the top-level object contains:
- `workflow_type`
- `requested_at`
- `monitoring_locations`
- `timeseries`

- [ ] **Step 2: Write the failing create-new-project JSON export test**

Add a test that exercises the station-discovery export path and asserts one workflow-level JSON file is written with:
- `workflow_type`
- `requested_at`
- `monitoring_locations`
- `qualifying_timeseries_metadata` or `field_measurements`

- [ ] **Step 3: Run the focused tests to verify they fail**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "combined_json or raw_json_export" -v`
Expected: FAIL because the current code writes flattened JSON arrays and `create-new-project` does not write this artifact yet.

### Task 2: Add frame-to-FeatureCollection export helpers

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing conversion-helper test**

Add a test that asserts a helper can convert `dataretrieval` frames into GeoJSON-like `FeatureCollection` objects with the expected ids, properties, and geometry.

- [ ] **Step 2: Run the focused helper test to verify it fails**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "dataframe_to_feature_collection" -v`
Expected: FAIL because the conversion helper does not exist yet.

- [ ] **Step 3: Implement the minimal conversion helper**

Implement functions that:
- accept `dataretrieval` frames
- produce GeoJSON-like `FeatureCollection` dictionaries
- preserve geometry when present and omit it where appropriate

- [ ] **Step 4: Re-run the helper test**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "dataframe_to_feature_collection" -v`
Expected: PASS

### Task 3: Add combined JSON writing support

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing export-helper test**

Add a test for a helper that writes a combined wrapper object and preserves nested `FeatureCollection` blocks unchanged.

- [ ] **Step 2: Run the focused export-helper test to verify it fails**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "combined_export_helper" -v`
Expected: FAIL because the helper does not exist yet.

- [ ] **Step 3: Implement the minimal JSON export helper**

Add a helper that writes:

```json
{
  "workflow_type": "...",
  "requested_at": "...",
  "...second-level raw payload keys...": {}
}
```

Keep CSV/parquet behavior unchanged.

- [ ] **Step 4: Re-run the export-helper test**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "combined_export_helper" -v`
Expected: PASS

### Task 4: Switch add-data JSON artifacts to the new combined raw format

**Files:**
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Verify the add-data combined JSON test is still failing for the right reason**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "add_data_combined_json" -v`
Expected: FAIL because `timeseries.py` is not yet building `FeatureCollection` blocks from `dataretrieval` frames.

- [ ] **Step 2: Implement the minimal add-data integration**

Update `get_usgs_timeseries(...)` to:
- keep the current DataFrame retrieval path
- fetch the monitoring-location frame through `dataretrieval`
- convert the station and observation frames into nested `FeatureCollection` blocks
- write one combined JSON artifact alongside CSV/parquet

- [ ] **Step 3: Re-run the add-data test**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "add_data_combined_json" -v`
Expected: PASS

### Task 5: Add create-new-project combined JSON artifacts

**Files:**
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Modify: `src/waterdata_toolbox_demo/cli.py`
- Modify: `src/waterdata_toolbox_demo/gui.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Verify the create-new-project combined JSON test is still failing for the right reason**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "create_project_combined_json" -v`
Expected: FAIL because no workflow-level combined JSON artifact is written yet.

- [ ] **Step 2: Implement the minimal create-new-project integration**

Update the workflow to:
- keep the current candidate/qualifying DataFrame logic
- convert filtered candidate and qualifying frames to nested `FeatureCollection` blocks
- write one workflow-level combined JSON file

- [ ] **Step 3: Re-run the create-new-project test**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "create_project_combined_json" -v`
Expected: PASS

### Task 6: Update docs and run the relevant regression slice

**Files:**
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Update package docs**

Document that JSON artifacts are now combined USGS-style wrapper objects built from `dataretrieval` outputs for both workflows.

- [ ] **Step 2: Run the relevant regression slice**

Run: `env UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "dataframe_to_feature_collection or combined_json or json_artifact or cli or gui" -v`
Expected: PASS
