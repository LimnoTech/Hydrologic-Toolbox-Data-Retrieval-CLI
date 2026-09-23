# Task 6 Waterdata Artifact Generation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the task-6 demo path retrieve USGS data through `dataretrieval.waterdata` and visibly write JSON, CSV, and parquet artifacts for the configured discharge example.

**Architecture:** Keep all `waterdata` integration inside [`helpers/usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py), with the notebook at [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb) acting as a thin demo layer that explicitly calls `get_usgs_timeseries(...)`, previews the returned frame, and renders artifact output details via shared helper formatting. Add a small extraction target in the helper for execution-level smoke tests so the user-facing task-6 flow can be exercised without executing the whole notebook every time.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval`, `pandas`, `pytest`, optional `pyarrow` or `fastparquet`

---

### Task 1: Harden Helper Artifact Export for Notebook Callers

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write the failing helper-path normalization test**

```python
def test_timeseries_accepts_string_output_dir_and_writes_artifacts(monkeypatch, tmp_path):
    def fake_daily(**kwargs):
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)

    payload = get_usgs_timeseries("02225500", "discharge", str(tmp_path))

    assert payload["files"]["json"].exists()
    assert payload["files"]["csv"].exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_timeseries_accepts_string_output_dir_and_writes_artifacts -v`
Expected: FAIL with an attribute error or path-handling failure when `output_dir` is a string

- [ ] **Step 3: Write the minimal helper change**

```python
from pathlib import Path


def export_timeseries_artifacts(frame, output_dir, workflow_type, station_id):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
```

- [ ] **Step 4: Extend the helper tests for partial-success output**

```python
def test_timeseries_returns_parquet_warning_without_losing_json_or_csv(monkeypatch, tmp_path):
    def fake_daily(**kwargs):
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    def fake_to_parquet(*args, **kwargs):
        raise ImportError("Missing optional dependency 'pyarrow'")

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    payload = get_usgs_timeseries("02225500", "discharge", tmp_path)

    assert payload["files"]["json"].exists()
    assert payload["files"]["csv"].exists()
    assert payload["files"]["parquet"] is None
    assert "pyarrow" in payload["files"]["parquet_error"]
```

- [ ] **Step 5: Run the focused helper tests**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_timeseries_accepts_string_output_dir_and_writes_artifacts tests/test_usgs_waterdata_demo.py::test_timeseries_returns_parquet_warning_without_losing_json_or_csv -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add helpers/usgs_waterdata_demo.py tests/test_usgs_waterdata_demo.py
git commit -m "Harden task 6 artifact export"
```

### Task 2: Add a Real Notebook Task-6 Retrieval Flow

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write the failing extraction-target test**

```python
def test_build_task6_demo_output_reports_artifacts_and_parquet_warning(monkeypatch, tmp_path):
    def fake_daily(**kwargs):
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    def fake_to_parquet(*args, **kwargs):
        raise ImportError("Missing optional dependency 'pyarrow'")

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    output = build_task6_demo_output(tmp_path)

    assert output["payload"]["files"]["json"].exists()
    assert output["payload"]["files"]["csv"].exists()
    assert output["artifact_messages"][0].endswith(".json")
    assert output["artifact_messages"][1].endswith(".csv")
    assert "pyarrow" in output["artifact_messages"][2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_reports_artifacts_and_parquet_warning -v`
Expected: FAIL with missing helper function or missing notebook-oriented reporting behavior

- [ ] **Step 3: Add the notebook extraction target in the helper**

```python
def build_task6_demo_output(output_dir=None):
    root = Path(__file__).resolve().parents[1]
    output_dir = root / DEMO_CONFIG["output_dir"] if output_dir is None else Path(output_dir)
    example = DEMO_CONFIG["example_stations"]["discharge"]
    payload = get_usgs_timeseries(
        example["station_id"],
        "discharge",
        output_dir,
        parameter_code=example["parameter_code"],
        date_range=DEMO_CONFIG["date_range"],
    )
    artifact_messages = format_artifact_messages(payload["files"])
    return {"payload": payload, "artifact_messages": artifact_messages}
```

- [ ] **Step 4: Add explicit artifact-report formatting**

```python
def format_artifact_messages(files):
    if not files:
        return ["No artifacts written because no records were returned."]
    if files["parquet"] is None:
        return [str(files["json"]), str(files["csv"]), files["parquet_error"]]
    return [str(files["json"]), str(files["csv"]), str(files["parquet"])]
```

- [ ] **Step 5: Update the notebook to show the real task-6 retrieval flow**

```python
from helpers.usgs_waterdata_demo import format_artifact_messages, get_usgs_timeseries

example = DEMO_CONFIG["example_stations"]["discharge"]
payload = get_usgs_timeseries(
    example["station_id"],
    "discharge",
    ROOT / DEMO_CONFIG["output_dir"],
    parameter_code=example["parameter_code"],
    date_range=DEMO_CONFIG["date_range"],
)
artifact_messages = format_artifact_messages(payload["files"])
payload["frame"].head()
artifact_messages
```

- [ ] **Step 6: Add a notebook-structure assertion that it uses the extraction target**

```python
def test_demo_notebook_uses_task6_extraction_target():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    code_sources = ["".join(cell.get("source", [])) for cell in notebook["cells"] if cell["cell_type"] == "code"]

    assert any("get_usgs_timeseries" in source for source in code_sources)
    assert any("artifact_messages" in source for source in code_sources)
    assert any('DEMO_CONFIG["example_stations"]["discharge"]' in source or "DEMO_CONFIG['example_stations']['discharge']" in source for source in code_sources)
    assert any('ROOT / DEMO_CONFIG["output_dir"]' in source or "ROOT / DEMO_CONFIG['output_dir']" in source for source in code_sources)
```

- [ ] **Step 7: Run the focused notebook/task-6 tests**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_reports_artifacts_and_parquet_warning tests/test_usgs_waterdata_demo.py::test_demo_notebook_uses_task6_extraction_target -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add helpers/usgs_waterdata_demo.py notebooks/usgs_waterdata_demo.ipynb tests/test_usgs_waterdata_demo.py
git commit -m "Add task 6 notebook retrieval flow"
```

### Task 3: Add Execution-Level Task-6 Smoke Tests

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write the failing parquet-warning execution-level smoke test**

```python
def test_build_task6_demo_output_writes_json_csv_and_reports_parquet_failure(monkeypatch, tmp_path):
    def fake_daily(**kwargs):
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    def fake_to_parquet(*args, **kwargs):
        raise ImportError("Missing optional dependency 'pyarrow'")

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    output = build_task6_demo_output(tmp_path)

    assert output["payload"]["files"]["json"].exists()
    assert output["payload"]["files"]["csv"].exists()
    assert output["artifact_messages"][0].endswith(".json")
    assert output["artifact_messages"][1].endswith(".csv")
    assert "pyarrow" in output["artifact_messages"][2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_writes_json_csv_and_reports_parquet_failure -v`
Expected: FAIL until the extraction target surfaces the parquet-warning branch correctly

- [ ] **Step 3: Write the failing no-records execution-level smoke test**

```python
def test_build_task6_demo_output_reports_when_no_artifacts_are_written(monkeypatch, tmp_path):
    def fake_daily(**kwargs):
        return pd.DataFrame(columns=["value", "observation_time"]), {"source": "daily"}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)

    output = build_task6_demo_output(tmp_path)

    assert output["payload"]["files"] == {}
    assert output["artifact_messages"] == ["No artifacts written because no records were returned."]
```

- [ ] **Step 4: Run test to verify it fails**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_reports_when_no_artifacts_are_written -v`
Expected: FAIL until the extraction target handles the empty-files path explicitly

- [ ] **Step 5: Add a helper-level assertion that the configured discharge example is used**

```python
def test_build_task6_demo_output_uses_configured_discharge_example(monkeypatch, tmp_path):
    captured = {}

    def fake_get_usgs_timeseries(station_id, workflow_type, output_dir, parameter_code=None, date_range=None):
        captured["station_id"] = station_id
        captured["workflow_type"] = workflow_type
        captured["parameter_code"] = parameter_code
        captured["date_range"] = date_range
        return {"frame": pd.DataFrame(), "records": [], "files": {}, "metadata": {}}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.get_usgs_timeseries", fake_get_usgs_timeseries)

    build_task6_demo_output(tmp_path)

    assert captured["station_id"] == DEMO_CONFIG["example_stations"]["discharge"]["station_id"]
    assert captured["workflow_type"] == "discharge"
    assert captured["parameter_code"] == DEMO_CONFIG["example_stations"]["discharge"]["parameter_code"]
    assert captured["date_range"] == DEMO_CONFIG["date_range"]
```

- [ ] **Step 6: Add a smoke test for the default configured output directory**

```python
def test_build_task6_demo_output_defaults_to_configured_output_dir(monkeypatch):
    def fake_daily(**kwargs):
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {"source": "daily"}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)

    output = build_task6_demo_output()

    expected_dir = ROOT / DEMO_CONFIG["output_dir"]
    assert output["payload"]["files"]["json"].parent == expected_dir
    assert output["payload"]["files"]["csv"].parent == expected_dir
```

- [ ] **Step 7: Run the four focused smoke tests**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_writes_json_csv_and_reports_parquet_failure tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_reports_when_no_artifacts_are_written tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_uses_configured_discharge_example tests/test_usgs_waterdata_demo.py::test_build_task6_demo_output_defaults_to_configured_output_dir -v`
Expected: PASS

- [ ] **Step 8: Adjust the implementation only if a smoke test exposes a remaining gap**

```python
# Keep the extraction target and artifact-message formatting aligned with parquet-warning, no-records, and default-output-dir paths.
```

- [ ] **Step 9: Run the targeted task-6 test slice**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py -k "task6 or timeseries or export or notebook or artifact" -v`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add helpers/usgs_waterdata_demo.py notebooks/usgs_waterdata_demo.ipynb tests/test_usgs_waterdata_demo.py
git commit -m "Verify task 6 artifact generation flow"
```

### Task 4: Final Verification

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Run the full notebook-demo test file**

Run: `python -m pytest tests/test_usgs_waterdata_demo.py -v`
Expected: PASS

- [ ] **Step 2: Optionally execute the notebook if dependencies are available**

Run: `jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`
Expected: successful execution with the task-6 cell showing either all artifact paths or a parquet warning plus JSON/CSV paths

- [ ] **Step 3: Review generated outputs**

```text
Check outputs/usgs_waterdata_demo for task-6 discharge artifacts created during notebook execution.
```

- [ ] **Step 4: Inspect the executed notebook output for visible artifact reporting**

```python
import json
from pathlib import Path

notebook = json.loads(Path("notebooks/usgs_waterdata_demo.ipynb").read_text())
text_outputs = []
for cell in notebook["cells"]:
    for output in cell.get("outputs", []):
        text = "".join(output.get("text", []))
        if text:
            text_outputs.append(text)

joined = "\n".join(text_outputs)
assert "outputs/usgs_waterdata_demo" in joined
assert ".json" in joined
assert ".csv" in joined
assert (".parquet" in joined) or ("parquet" in joined.lower())
```

- [ ] **Step 5: Commit**

```bash
git add helpers/usgs_waterdata_demo.py notebooks/usgs_waterdata_demo.ipynb tests/test_usgs_waterdata_demo.py
git commit -m "Complete task 6 waterdata artifact flow"
```
