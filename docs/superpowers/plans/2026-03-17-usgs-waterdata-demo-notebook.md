# USGS Water Data Demo Notebook Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a demo notebook that replaces the legacy NWIS/.NET station-discovery and time-series workflow with modern `dataretrieval-python` retrieval plus JSON/CSV/Parquet exports.

**Architecture:** Keep the deliverable notebook-first, but place the reusable routing, normalization, and export logic in [`helpers/usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py). The notebook at [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb) will focus on configuration, legacy-to-modern mapping, visible demo cells, and displaying outputs from the helper module.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval`, `pandas`, `pytest`, optional `pyarrow` or `fastparquet`

---

### Task 1: Align the Repo for Testable Notebook Work

**Files:**
- Modify: `.gitignore`
- Modify: `requirements.txt`
- Modify: `helpers/__init__.py`
- Create: `tests/test_usgs_waterdata_demo.py`
- Create: `outputs/usgs_waterdata_demo/.gitkeep`

- [ ] **Step 1: Write the failing repo-layout smoke test**

```python
from pathlib import Path


def test_expected_demo_files_exist():
    assert Path("helpers/__init__.py").exists()
    assert Path("helpers/usgs_waterdata_demo.py").exists()
    assert Path("notebooks/usgs_waterdata_demo.ipynb").exists()
    assert Path("requirements.txt").exists()
    assert Path("outputs/usgs_waterdata_demo/.gitkeep").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_expected_demo_files_exist -v`
Expected: FAIL because `outputs/usgs_waterdata_demo/.gitkeep` is not created yet

- [ ] **Step 3: Update `.gitignore` so the plan’s test file can be tracked**

```gitignore
tests/
!tests/
tests/*
!tests/test_usgs_waterdata_demo.py
```

- [ ] **Step 4: Add the minimal tracked test file and output placeholder**

```text
tests/test_usgs_waterdata_demo.py
outputs/usgs_waterdata_demo/.gitkeep
```

- [ ] **Step 5: Ensure dependencies include the notebook and test stack**

```text
dataretrieval
pandas
pytest
jupyter
```

- [ ] **Step 6: Run test to verify it passes**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_expected_demo_files_exist -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add .gitignore requirements.txt helpers/__init__.py tests/test_usgs_waterdata_demo.py outputs/usgs_waterdata_demo/.gitkeep
git commit -m "Prepare repo for notebook demo tests"
```

### Task 2: Add Deterministic Demo Configuration and Mapping Metadata

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Modify: `notebooks/usgs_waterdata_demo.ipynb`

- [ ] **Step 1: Write the failing configuration test**

```python
from helpers.usgs_waterdata_demo import DEMO_CONFIG, LEGACY_CALLS


def test_demo_config_and_mapping_cover_all_workflow_types():
    assert set(DEMO_CONFIG["example_stations"]) == {"discharge", "gw_daily", "gw_periodic"}
    assert set(LEGACY_CALLS) == {"discharge", "gw_daily", "gw_periodic"}
    assert DEMO_CONFIG["date_range"] == ("1880-01-01", "2100-01-01")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_config_and_mapping_cover_all_workflow_types -v`
Expected: FAIL with missing import or missing-name errors

- [ ] **Step 3: Add deterministic configuration and mapping metadata to the helper module**

```python
DEMO_CONFIG = {
    "bbox": (-82.859, 31.899, -82.013, 32.947),
    "output_dir": "outputs/usgs_waterdata_demo",
    "date_range": ("1880-01-01", "2100-01-01"),
    "example_stations": {
        "discharge": {"station_id": "02225500", "parameter_code": "00060"},
        "gw_daily": {"station_id": "324209082430201", "parameter_code": "72019"},
        "gw_periodic": {"station_id": "410947071344803", "parameter_code": "72019"},
    },
}

LEGACY_CALLS = {
    "discharge": {"legacy_steps": ["New Project station discovery", "Adding Data to Project"]},
    "gw_daily": {"legacy_steps": ["New Project station discovery", "Adding Data to Project"]},
    "gw_periodic": {"legacy_steps": ["New Project station discovery", "Adding Data to Project"]},
}

NOTEBOOK_MAPPING_ROWS = [
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "discharge",
        "legacy_intent": "Find surface-water stations in a bounding box",
        "modern_helper_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=ST, parameter_code=00060",
        "expected_output_shape": "DataFrame of discharge-capable stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_daily",
        "legacy_intent": "Find groundwater stations with daily series in a bounding box",
        "modern_helper_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater daily stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Find groundwater stations with periodic observations in a bounding box",
        "modern_helper_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_field_measurements",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater periodic stations",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "discharge",
        "legacy_intent": "Retrieve discharge time series for a selected station",
        "modern_helper_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "parameter_code=00060, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_daily",
        "legacy_intent": "Retrieve groundwater daily time series for a selected station",
        "modern_helper_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Retrieve groundwater periodic measurements for a selected station",
        "modern_helper_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_field_measurements",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
]
```

- [ ] **Step 4: Add notebook setup cells that import and display the configuration**

```python
import sys
from pathlib import Path

ROOT = Path.cwd().resolve().parent if Path.cwd().name == "notebooks" else Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from helpers.usgs_waterdata_demo import DEMO_CONFIG, LEGACY_CALLS, NOTEBOOK_MAPPING_ROWS

DEMO_CONFIG
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_config_and_mapping_cover_all_workflow_types -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add helpers/usgs_waterdata_demo.py tests/test_usgs_waterdata_demo.py notebooks/usgs_waterdata_demo.ipynb
git commit -m "Add deterministic demo configuration"
```

### Task 3: Implement Station Discovery Routing and Normalization

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Modify: `notebooks/usgs_waterdata_demo.ipynb`

- [ ] **Step 1: Write the failing station-discovery routing test**

```python
import pandas as pd

from helpers.usgs_waterdata_demo import get_usgs_stations_in_bbox


def test_station_discovery_intersects_service_results_and_tags_workflow(monkeypatch):
    monitoring_calls = []
    metadata_calls = []
    field_calls = []

    def fake_monitoring_locations(**kwargs):
        monitoring_calls.append(kwargs)
        if kwargs["site_type_code"] == "ST":
            frame = pd.DataFrame(
                [
                    {"monitoring_location_id": "USGS-1", "location_name": "Surface One", "site_type_code": "ST"},
                    {"monitoring_location_id": "USGS-9", "location_name": "Surface Nine", "site_type_code": "ST"},
                ]
            )
        else:
            frame = pd.DataFrame(
                [
                    {"monitoring_location_id": "USGS-2", "location_name": "GW Two", "site_type_code": "GW"},
                    {"monitoring_location_id": "USGS-3", "location_name": "GW Three", "site_type_code": "GW"},
                ]
            )
        return frame, {}

    def fake_metadata(**kwargs):
        metadata_calls.append(kwargs)
        if kwargs.get("parameter_code") == "00060":
            frame = pd.DataFrame([{"monitoring_location_id": "USGS-1"}])
        else:
            frame = pd.DataFrame([{"monitoring_location_id": "USGS-2"}])
        return frame, {}

    def fake_field_measurements(**kwargs):
        field_calls.append(kwargs)
        return pd.DataFrame([{"monitoring_location_id": "USGS-3"}]), {}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_monitoring_locations", fake_monitoring_locations)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_time_series_metadata", fake_metadata)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_field_measurements", fake_field_measurements)

    result = get_usgs_stations_in_bbox(
        (-82.859, 31.899, -82.013, 32.947),
        ["discharge", "gw_daily", "gw_periodic"],
    )

    assert set(result) == {"discharge", "gw_daily", "gw_periodic"}
    assert result["discharge"]["monitoring_location_id"].tolist() == ["USGS-1"]
    assert result["gw_daily"]["monitoring_location_id"].tolist() == ["USGS-2"]
    assert result["gw_periodic"]["monitoring_location_id"].tolist() == ["USGS-3"]
    assert set(["workflow_type", "monitoring_location_id"]) <= set(result["discharge"].columns)
    assert monitoring_calls[0]["site_type_code"] == "ST"
    assert monitoring_calls[1]["site_type_code"] == "GW"
    assert metadata_calls[0]["parameter_code"] == "00060"
    assert field_calls[0]["bBox"] == (-82.859, 31.899, -82.013, 32.947)


def test_station_discovery_returns_empty_frame_when_no_candidates_match(monkeypatch):
    def fake_monitoring_locations(**kwargs):
        return pd.DataFrame([{"monitoring_location_id": "USGS-9"}]), {}

    def fake_metadata(**kwargs):
        return pd.DataFrame([{"monitoring_location_id": "USGS-1"}]), {}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_monitoring_locations", fake_monitoring_locations)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_time_series_metadata", fake_metadata)

    result = get_usgs_stations_in_bbox((-82.859, 31.899, -82.013, 32.947), ["discharge"])

    assert result["discharge"].empty
    assert "workflow_type" in result["discharge"].columns
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_station_discovery_intersects_service_results_and_tags_workflow tests/test_usgs_waterdata_demo.py::test_station_discovery_returns_empty_frame_when_no_candidates_match -v`
Expected: FAIL because `get_usgs_stations_in_bbox` does not exist yet

- [ ] **Step 3: Implement workflow-specific station-query helpers**

```python
def _get_discharge_stations(bbox):
    ...


def _get_groundwater_daily_stations(bbox):
    ...


def _get_groundwater_periodic_stations(bbox):
    ...
```

- [ ] **Step 4: Add the shared intersection and normalization logic**

```python
candidate_ids = set(candidate_frame["monitoring_location_id"])
qualifying_ids = set(qualifying_frame["monitoring_location_id"])
frame = candidate_frame[candidate_frame["monitoring_location_id"].isin(candidate_ids & qualifying_ids)].copy()
frame["workflow_type"] = workflow_type
frame = frame.drop_duplicates(subset=["monitoring_location_id"])
frame = frame.sort_values("monitoring_location_id").reset_index(drop=True)
```

- [ ] **Step 5: Preserve a stable empty-frame contract when no stations qualify**

```python
if frame.empty and "workflow_type" not in frame.columns:
    frame["workflow_type"] = pd.Series(dtype="object")
```

- [ ] **Step 6: Implement `get_usgs_stations_in_bbox` as the thin orchestrator**

```python
def get_usgs_stations_in_bbox(bbox, data_types):
    handlers = {
        "discharge": _get_discharge_stations,
        "gw_daily": _get_groundwater_daily_stations,
        "gw_periodic": _get_groundwater_periodic_stations,
    }
    return {workflow_type: handlers[workflow_type](bbox) for workflow_type in data_types}
```

- [ ] **Step 7: Add notebook cells that show row counts and sample records**

```python
station_results = get_usgs_stations_in_bbox(DEMO_CONFIG["bbox"], ["discharge", "gw_daily", "gw_periodic"])
for workflow_type, frame in station_results.items():
    print(workflow_type, len(frame))
    display(frame.head())
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_station_discovery_intersects_service_results_and_tags_workflow tests/test_usgs_waterdata_demo.py::test_station_discovery_returns_empty_frame_when_no_candidates_match -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add helpers/usgs_waterdata_demo.py tests/test_usgs_waterdata_demo.py notebooks/usgs_waterdata_demo.ipynb
git commit -m "Add station discovery helpers"
```

### Task 4: Implement Time-Series Routing, Exports, and Demo-Safe Error Handling

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write the failing time-series routing test**

```python
import pandas as pd

from helpers.usgs_waterdata_demo import get_usgs_timeseries


def test_timeseries_routes_expected_service_calls_and_returns_contract(monkeypatch, tmp_path):
    calls = []

    def fake_daily(**kwargs):
        calls.append(("daily", kwargs))
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    def fake_field_measurements(**kwargs):
        calls.append(("field", kwargs))
        return pd.DataFrame([{"value": 2.0, "observation_time": "2020-01-02"}]), {"source": "field"}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_field_measurements", fake_field_measurements)

    discharge_payload = get_usgs_timeseries("02225500", "discharge", tmp_path)
    gw_daily_payload = get_usgs_timeseries("324209082430201", "gw_daily", tmp_path, parameter_code="72019")
    gw_periodic_payload = get_usgs_timeseries("410947071344803", "gw_periodic", tmp_path, parameter_code="72019")

    assert [name for name, _ in calls] == ["daily", "daily", "field"]
    assert calls[0][1]["parameter_code"] == "00060"
    assert calls[1][1]["parameter_code"] == "72019"
    assert calls[0][1]["start"] == "1880-01-01"
    assert calls[0][1]["end"] == "2100-01-01"
    assert discharge_payload["records"][0]["workflow_type"] == "discharge"
    assert gw_daily_payload["records"][0]["workflow_type"] == "gw_daily"
    assert gw_periodic_payload["records"][0]["workflow_type"] == "gw_periodic"
    assert {"frame", "records", "files", "metadata"} <= set(discharge_payload)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_timeseries_routes_expected_service_calls_and_returns_contract -v`
Expected: FAIL because `get_usgs_timeseries` does not exist yet

- [ ] **Step 3: Write the failing export behavior tests**

```python
import json
import pandas as pd

from helpers.usgs_waterdata_demo import export_timeseries_artifacts


def test_export_writes_json_and_csv_and_tracks_parquet(tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].exists()
    assert file_paths["csv"].exists()
    assert "parquet" in file_paths
    loaded = json.loads(file_paths["json"].read_text())
    assert loaded[0]["station_id"] == "A"


def test_export_keeps_json_and_csv_when_parquet_is_unavailable(monkeypatch, tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    def fake_to_parquet(*args, **kwargs):
        raise ImportError("Missing optional dependency 'pyarrow'")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].exists()
    assert file_paths["csv"].exists()
    assert file_paths["parquet"] is None
    assert "pyarrow" in file_paths["parquet_error"]


def test_export_uses_deterministic_filenames(tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].name == "discharge_A.json"
    assert file_paths["csv"].name == "discharge_A.csv"


def test_timeseries_returns_empty_frame_contract_when_service_has_no_rows(monkeypatch, tmp_path):
    def fake_daily(**kwargs):
        return pd.DataFrame(columns=["value"]), {"source": "daily"}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)

    payload = get_usgs_timeseries("02225500", "discharge", tmp_path)

    assert payload["frame"].empty
    assert payload["records"] == []
    assert payload["metadata"]["source"] == "daily"
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_timeseries_routes_expected_service_calls_and_returns_contract tests/test_usgs_waterdata_demo.py::test_export_writes_json_and_csv_and_tracks_parquet tests/test_usgs_waterdata_demo.py::test_timeseries_returns_empty_frame_contract_when_service_has_no_rows -v`
Expected: FAIL because the helper functions do not exist yet

- [ ] **Step 5: Implement `get_usgs_timeseries` with explicit workflow routing**

```python
def get_usgs_timeseries(station_id, workflow_type, output_dir, parameter_code=None, date_range=("1880-01-01", "2100-01-01")):
    if workflow_type in {"discharge", "gw_daily"}:
        frame, metadata = wd.get_daily(
            monitoring_location_id=station_id,
            parameter_code="00060" if workflow_type == "discharge" else parameter_code,
            start=date_range[0],
            end=date_range[1],
        )
    elif workflow_type == "gw_periodic":
        frame, metadata = wd.get_field_measurements(
            monitoring_location_id=station_id,
            parameter_code=parameter_code,
            start=date_range[0],
            end=date_range[1],
        )
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")
```

- [ ] **Step 6: Add normalization and the exported return contract**

```python
frame = frame.reset_index(drop=True).copy()
frame["station_id"] = station_id
frame["workflow_type"] = workflow_type
records = frame.to_dict(orient="records")
file_paths = export_timeseries_artifacts(frame, Path(output_dir), workflow_type, station_id)
return {"frame": frame, "records": records, "files": file_paths, "metadata": metadata}
```

- [ ] **Step 7: Add demo-safe empty-result handling and readable warnings**

```python
if frame.empty:
    return {
        "frame": frame,
        "records": [],
        "files": {},
        "metadata": {**metadata, "warning": f"No records returned for {workflow_type} {station_id}"},
    }
```

- [ ] **Step 8: Implement the export helper with graceful Parquet fallback**

```python
def export_timeseries_artifacts(frame, output_dir, workflow_type, station_id):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{workflow_type}_{station_id}.json"
    csv_path = output_dir / f"{workflow_type}_{station_id}.csv"
    parquet_path = output_dir / f"{workflow_type}_{station_id}.parquet"

    frame.to_json(json_path, orient="records", indent=2)
    frame.to_csv(csv_path, index=False)

    file_paths = {"json": json_path, "csv": csv_path, "parquet": parquet_path, "parquet_error": None}
    try:
        frame.to_parquet(parquet_path, index=False)
    except Exception as exc:
        file_paths["parquet"] = None
        file_paths["parquet_error"] = str(exc)

    return file_paths
```

- [ ] **Step 9: Add a notebook-facing warning pattern for empty discovery and retrieval results**

```python
if frame.empty:
    print(f"{workflow_type}: no results returned for the configured demo inputs")
else:
    display(frame.head())
```

- [ ] **Step 10: Run tests to verify they pass**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_timeseries_routes_expected_service_calls_and_returns_contract tests/test_usgs_waterdata_demo.py::test_export_writes_json_and_csv_and_tracks_parquet tests/test_usgs_waterdata_demo.py::test_export_keeps_json_and_csv_when_parquet_is_unavailable tests/test_usgs_waterdata_demo.py::test_export_uses_deterministic_filenames tests/test_usgs_waterdata_demo.py::test_timeseries_returns_empty_frame_contract_when_service_has_no_rows -v`
Expected: PASS

- [ ] **Step 11: Commit**

```bash
git add helpers/usgs_waterdata_demo.py tests/test_usgs_waterdata_demo.py
git commit -m "Add timeseries and export helpers"
```

### Task 5: Build the Notebook Narrative and Demo Cells

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`

- [ ] **Step 1: Add the title and migration-context markdown cells**

```markdown
# USGS Water Data Demo

This notebook demonstrates how modern Python retrieval calls can replace the legacy NWIS/.NET workflow for station discovery and time-series retrieval.
```

- [ ] **Step 2: Add the imports and repo-root setup cell**

```python
import sys
from pathlib import Path

import pandas as pd
from IPython.display import display

ROOT = Path.cwd().resolve().parent if Path.cwd().name == "notebooks" else Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from helpers.usgs_waterdata_demo import (
    DEMO_CONFIG,
    LEGACY_CALLS,
    NOTEBOOK_MAPPING_ROWS,
    get_usgs_stations_in_bbox,
    get_usgs_timeseries,
)
```

- [ ] **Step 3: Add the visible configuration display cell**

```python
DEMO_CONFIG
```

- [ ] **Step 4: Add the legacy-to-modern mapping section**

```python
mapping_frame = pd.DataFrame(NOTEBOOK_MAPPING_ROWS)
display(mapping_frame)
```

- [ ] **Step 5: Add the station-discovery execution section**

```python
station_results = get_usgs_stations_in_bbox(DEMO_CONFIG["bbox"], ["discharge", "gw_daily", "gw_periodic"])
for workflow_type, frame in station_results.items():
    print(f"{workflow_type}: {len(frame)} stations")
    if frame.empty:
        print("No stations returned for this workflow type")
    else:
        display(frame.head())
```

- [ ] **Step 6: Add the deterministic retrieval and export section**

```python
timeseries_results = {}
for workflow_type, station_config in DEMO_CONFIG["example_stations"].items():
    timeseries_results[workflow_type] = get_usgs_timeseries(
        station_config["station_id"],
        workflow_type,
        DEMO_CONFIG["output_dir"],
        parameter_code=station_config["parameter_code"],
        date_range=DEMO_CONFIG["date_range"],
    )
    print(workflow_type, timeseries_results[workflow_type]["files"])
    if timeseries_results[workflow_type]["frame"].empty:
        print(timeseries_results[workflow_type]["metadata"].get("warning"))
    else:
        display(timeseries_results[workflow_type]["frame"].head())
```

- [ ] **Step 7: Add closing markdown about limits and next migration steps**

```markdown
## Notes and Limits

- This demo favors readability over framework-level abstraction.
- Shapefile and projection workflows are intentionally out of scope.
- The helper module can be reused for follow-on migration work if the notebook proves the workflow.
```

- [ ] **Step 8: Commit**

```bash
git add notebooks/usgs_waterdata_demo.ipynb
git commit -m "Build notebook migration walkthrough"
```

### Task 6: Run Verification and Capture the Final Execution Pass

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Run the full automated helper test file**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py -v`
Expected: PASS

- [ ] **Step 2: Execute the notebook top-to-bottom in the project environment**

Run: `jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`
Expected: PASS with the notebook updated in place and export artifacts written under `outputs/usgs_waterdata_demo/`

- [ ] **Step 3: Inspect generated outputs and confirm deterministic filenames**

Run: `find outputs/usgs_waterdata_demo -maxdepth 1 -type f | sort`
Expected: JSON and CSV files for each configured workflow, plus Parquet files when an engine is available

- [ ] **Step 4: If notebook execution reveals unclear markdown or brittle cells, make the smallest doc-only fixes**

```text
Adjust markdown wording, display order, or cell output framing without changing the helper contracts.
```

- [ ] **Step 5: Re-run verification after any notebook polish**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py -v`
Expected: PASS

Run: `jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add helpers/usgs_waterdata_demo.py tests/test_usgs_waterdata_demo.py notebooks/usgs_waterdata_demo.ipynb outputs/usgs_waterdata_demo
git commit -m "Verify notebook demo execution"
```
