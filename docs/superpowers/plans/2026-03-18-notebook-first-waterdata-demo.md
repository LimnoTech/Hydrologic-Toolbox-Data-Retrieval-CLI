# Notebook-First Waterdata Demo Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the USGS waterdata demo so the notebook itself contains the real `dataretrieval.waterdata` API usage for the `Creating New Project` and `Adding Data to Project` sections, while `helpers/` remains a small support-only module.

**Architecture:** Move demo-visible `waterdata` retrieval logic out of [`helpers/usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py) and into notebook-local functions inside [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb). Keep only shared config, mapping metadata, and export/report helpers in the support module, and update tests to treat the notebook as the primary behavior surface for retrieval.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval.waterdata`, `pandas`, `pytest`, `uv`, optional `pyarrow`

---

## File Map

- [`helpers/usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py)
  Responsibility: support-only module for config, mapping rows, export writing, and artifact message formatting. It should not own demo retrieval entry points after this refactor.
- [`helpers/__init__.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/__init__.py)
  Responsibility: remain minimal and consistent with the trimmed helper surface.
- [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb)
  Responsibility: own the real `waterdata` API demo functions, explain how each `waterdata` call works, and render both legacy workflow sections.
- [`tests/test_usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py)
  Responsibility: verify notebook-local retrieval ownership, support-only helper boundaries, export helper behavior, and executed notebook output.

**User Constraint:** Do not create commits during this work. Leave changes uncommitted.

### Task 1: Add Failing Tests for Notebook-Owned `waterdata` Retrieval Functions

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write failing tests that assert the notebook owns the demo retrieval functions**

```python
def test_demo_notebook_defines_local_waterdata_retrieval_functions():
    sources = get_demo_notebook_sources("code")

    assert any("def get_usgs_stations_in_bbox(" in source for source in sources)
    assert any("def get_usgs_timeseries(" in source for source in sources)
    assert any("from dataretrieval import waterdata as wd" in source for source in sources)


def test_helper_module_no_longer_owns_demo_retrieval_entry_points():
    import helpers.usgs_waterdata_demo as demo_helpers

    assert not hasattr(demo_helpers, "get_usgs_stations_in_bbox")
    assert not hasattr(demo_helpers, "get_usgs_timeseries")
    assert not hasattr(demo_helpers, "build_task6_demo_output")
```

- [ ] **Step 2: Write failing tests that assert notebook API notes exist near `waterdata` usage**

```python
def test_demo_notebook_explains_waterdata_station_discovery_usage():
    sources = get_demo_notebook_sources("markdown") + get_demo_notebook_sources("code")
    combined = "\n".join(sources)

    assert "get_monitoring_locations" in combined
    assert "get_time_series_metadata" in combined
    assert "get_field_measurements" in combined


def test_demo_notebook_explains_waterdata_timeseries_usage():
    sources = get_demo_notebook_sources("markdown") + get_demo_notebook_sources("code")
    combined = "\n".join(sources)

    assert "get_daily" in combined
    assert "parameter_code" in combined
    assert "time" in combined
```

- [ ] **Step 3: Run the targeted tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_waterdata_retrieval_functions tests/test_usgs_waterdata_demo.py::test_helper_module_no_longer_owns_demo_retrieval_entry_points tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_waterdata_station_discovery_usage tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_waterdata_timeseries_usage -v`

Expected: FAIL because the notebook currently imports helper-owned retrieval functions and the helper module still owns those entry points.

- [ ] **Step 4: Add notebook-local retrieval skeletons and explanatory notes**

```python
from dataretrieval import waterdata as wd


def get_usgs_stations_in_bbox(bbox, workflow_types):
    """Use waterdata station-discovery calls to find workflow-specific stations."""
    raise NotImplementedError


def get_usgs_timeseries(station_id, workflow_type, output_dir, parameter_code=None, date_range=("1880-01-01", "2100-01-01")):
    """Use waterdata daily/field-measurement calls to retrieve and export demo time series."""
    raise NotImplementedError
```

- [ ] **Step 5: Run the targeted tests to verify the ownership/notes checks pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_waterdata_retrieval_functions tests/test_usgs_waterdata_demo.py::test_helper_module_no_longer_owns_demo_retrieval_entry_points tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_waterdata_station_discovery_usage tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_waterdata_timeseries_usage -v`

Expected: PASS

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 2: Trim `helpers/usgs_waterdata_demo.py` to Support-Only Responsibilities

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `helpers/__init__.py`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write failing helper-boundary tests**

```python
def test_helper_module_support_surface_is_config_and_export_only():
    import helpers.usgs_waterdata_demo as demo_helpers

    assert hasattr(demo_helpers, "DEMO_CONFIG")
    assert hasattr(demo_helpers, "LEGACY_CALLS")
    assert hasattr(demo_helpers, "NOTEBOOK_MAPPING_ROWS")
    assert hasattr(demo_helpers, "export_timeseries_artifacts")
    assert hasattr(demo_helpers, "format_artifact_messages")
    assert not hasattr(demo_helpers, "get_usgs_stations_in_bbox")
    assert not hasattr(demo_helpers, "get_usgs_timeseries")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_helper_module_support_surface_is_config_and_export_only -v`

Expected: FAIL because retrieval functions still live in the helper module.

- [ ] **Step 3: Remove demo retrieval functions from the helper module**

```python
# Keep in helpers/usgs_waterdata_demo.py:
DEMO_CONFIG = {...}
LEGACY_CALLS = {...}
NOTEBOOK_MAPPING_ROWS = [...]

def export_timeseries_artifacts(...):
    ...

def format_artifact_messages(...):
    ...
```

Remove:

```python
def get_usgs_stations_in_bbox(...): ...
def get_usgs_timeseries(...): ...
def build_task6_demo_output(...): ...
def _get_discharge_stations(...): ...
def _get_groundwater_daily_stations(...): ...
def _get_groundwater_periodic_stations(...): ...
def _normalize_monitoring_location_id(...): ...
def _call_waterdata_with_filtered_datetime_warning(...): ...
```

- [ ] **Step 4: Update helper imports/tests to match the trimmed surface**

```python
from helpers.usgs_waterdata_demo import (
    DEMO_CONFIG,
    LEGACY_CALLS,
    NOTEBOOK_MAPPING_ROWS,
    export_timeseries_artifacts,
    format_artifact_messages,
)
```

- [ ] **Step 5: Run helper-support tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_helper_module_support_surface_is_config_and_export_only tests/test_usgs_waterdata_demo.py::test_export_writes_json_and_csv_and_tracks_parquet tests/test_usgs_waterdata_demo.py::test_export_keeps_json_and_csv_when_parquet_is_unavailable tests/test_usgs_waterdata_demo.py::test_export_uses_deterministic_filenames tests/test_usgs_waterdata_demo.py::test_format_artifact_messages_reports_empty_files tests/test_usgs_waterdata_demo.py::test_format_artifact_messages_reports_parquet_warning -v`

Expected: PASS

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 3: Move Station Discovery `waterdata` Logic into the Notebook

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write failing notebook-function tests for local station discovery**

```python
def test_notebook_local_station_discovery_uses_waterdata_calls(monkeypatch):
    calls = []

    def fake_monitoring_locations(**kwargs):
        calls.append(("monitoring", kwargs))
        return pd.DataFrame([{"monitoring_location_id": "USGS-1", "site_type_code": "ST"}]), {}

    def fake_metadata(**kwargs):
        calls.append(("metadata", kwargs))
        return pd.DataFrame([{"monitoring_location_id": "USGS-1"}]), {}

    def fake_field_measurements(**kwargs):
        calls.append(("field", kwargs))
        return pd.DataFrame([{"monitoring_location_id": "USGS-3"}]), {}

    get_usgs_stations_in_bbox = load_demo_notebook_function(
        "get_usgs_stations_in_bbox",
        {"wd": SimpleNamespace(
            get_monitoring_locations=fake_monitoring_locations,
            get_time_series_metadata=fake_metadata,
            get_field_measurements=fake_field_measurements,
        ), "pd": pd},
    )

    result = get_usgs_stations_in_bbox(DEMO_CONFIG["bbox"], ["discharge", "gw_daily", "gw_periodic"])

    assert set(result) == {"discharge", "gw_daily", "gw_periodic"}
    assert [name for name, _ in calls] == ["monitoring", "metadata", "monitoring", "metadata", "monitoring", "field"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_notebook_local_station_discovery_uses_waterdata_calls -v`

Expected: FAIL because the notebook does not yet own the real station-discovery logic.

- [ ] **Step 3: Implement notebook-local station discovery with explanatory notes**

```python
from dataretrieval import waterdata as wd

def _normalize_station_frame(candidate_frame, qualifying_frame, workflow_type):
    ...


def get_usgs_stations_in_bbox(bbox, workflow_types):
    """waterdata station discovery:
    - get_monitoring_locations(...): all stations in bbox
    - get_time_series_metadata(...): stations with daily series
    - get_field_measurements(...): stations with periodic measurements
    """
    ...
```

- [ ] **Step 4: Update the `Creating New Project` render cell to call the notebook-local function directly**

```python
create_section_results = get_usgs_stations_in_bbox(
    DEMO_CONFIG["bbox"],
    ["discharge", "gw_daily", "gw_periodic"],
)
```

- [ ] **Step 5: Run the notebook station-discovery tests and render test**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_notebook_local_station_discovery_uses_waterdata_calls tests/test_usgs_waterdata_demo.py::test_demo_notebook_render_create_section_uses_station_discovery_only -v`

Expected: PASS

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 4: Move Time-Series `waterdata` Logic into the Notebook and Reverify End to End

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write failing notebook-function tests for local time-series retrieval**

```python
def test_notebook_local_timeseries_uses_waterdata_calls_and_exports(monkeypatch, tmp_path):
    calls = []

    def fake_daily(**kwargs):
        calls.append(("daily", kwargs))
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    get_usgs_timeseries = load_demo_notebook_function(
        "get_usgs_timeseries",
        {
            "wd": SimpleNamespace(get_daily=fake_daily, get_field_measurements=None),
            "export_timeseries_artifacts": export_timeseries_artifacts,
            "pd": pd,
        },
    )

    payload = get_usgs_timeseries("02225500", "discharge", tmp_path)

    assert calls[0][1]["time"] == ["1880-01-01", "2100-01-01"]
    assert payload["files"]["json"].exists()
    assert payload["files"]["csv"].exists()
```

- [ ] **Step 2: Add a failing warning-suppression test at the notebook-function level**

```python
def test_notebook_local_timeseries_suppresses_infer_format_warning(monkeypatch, tmp_path):
    ...
```

- [ ] **Step 3: Run the targeted tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_notebook_local_timeseries_uses_waterdata_calls_and_exports tests/test_usgs_waterdata_demo.py::test_notebook_local_timeseries_suppresses_infer_format_warning -v`

Expected: FAIL because the notebook does not yet own the real time-series retrieval/export logic.

- [ ] **Step 4: Implement notebook-local time-series retrieval and notes**

```python
def _normalize_monitoring_location_id(station_id):
    ...


def _call_waterdata_with_filtered_datetime_warning(function, **kwargs):
    ...


def get_usgs_timeseries(station_id, workflow_type, output_dir, parameter_code=None, date_range=("1880-01-01", "2100-01-01")):
    """waterdata time-series retrieval:
    - get_daily(...): daily discharge and groundwater daily values
    - get_field_measurements(...): groundwater periodic measurements
    Important arguments:
    - monitoring_location_id
    - parameter_code
    - time=[start_date, end_date]
    """
    ...
```

- [ ] **Step 5: Update the add-data render cell to call the notebook-local function and keep current output behavior**

```python
add_data_results = run_add_data_to_project_section(
    DEMO_CONFIG["example_stations"],
    ROOT / DEMO_CONFIG["output_dir"],
    DEMO_CONFIG["date_range"],
)
```

- [ ] **Step 6: Re-execute the notebook end to end**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter --with pandas --with dataretrieval --with pyarrow jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`

Expected: PASS and refreshed outputs in `outputs/usgs_waterdata_demo`

- [ ] **Step 7: Run the full demo test file**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py -v`

Expected: PASS

- [ ] **Step 8: Inspect output files for all three workflows**

Run: `ls -1 outputs/usgs_waterdata_demo`

Expected:

```text
discharge_02225500.csv
discharge_02225500.json
discharge_02225500.parquet
gw_daily_324209082430201.csv
gw_daily_324209082430201.json
gw_daily_324209082430201.parquet
gw_periodic_410947071344803.csv
gw_periodic_410947071344803.json
gw_periodic_410947071344803.parquet
```

- [ ] **Step 9: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```
