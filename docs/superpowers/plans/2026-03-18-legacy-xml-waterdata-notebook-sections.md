# Legacy XML Waterdata Notebook Sections Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the USGS Water Data demo notebook so it explicitly recreates the legacy `Creating New Project` and `Adding Data to Project` XML workflow sections using `dataretrieval.waterdata` for `discharge`, `gw_daily`, and `gw_periodic`.

**Architecture:** Keep [`helpers/usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py) as the low-level adapter for station discovery, time-series retrieval, normalization, and artifact formatting. Put the legacy-section orchestration helpers directly inside [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb) so the notebook reads like the original XML workflow while still reusing the tested helper functions. Extend [`tests/test_usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py) to verify notebook structure, loop behavior, partial-failure handling, and executed-notebook outputs.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval`, `pandas`, `pytest`, `uv`, optional `pyarrow`

---

## File Map

- [`helpers/usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py)
  Responsibility: keep low-level `waterdata` calls, station-id normalization, export writing, and artifact-message formatting. Do not add new top-level workflow orchestration helpers here.
- [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb)
  Responsibility: define the two notebook-local orchestration helpers, add the two legacy-replacement sections, and display results in legacy-workflow order.
- [`tests/test_usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py)
  Responsibility: verify notebook structure, notebook-local helper behavior via extracted source, helper-module contracts, and executed-notebook output.

**User Constraint:** Do not create commits during this work. Leave changes uncommitted.

### Task 1: Add Failing Notebook-Structure Tests for the Two Legacy Sections

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write the failing notebook-structure tests**

```python
def test_demo_notebook_contains_legacy_workflow_sections():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    markdown_sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "markdown"
    ]

    assert any("Creating New Project" in source for source in markdown_sources)
    assert any("Adding Data to Project" in source for source in markdown_sources)


def test_demo_notebook_orders_legacy_sections_after_mapping():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    headings = [
        "".join(cell.get("source", [])).strip().lstrip("# ").strip()
        for cell in notebook["cells"]
        if cell["cell_type"] == "markdown"
    ]

    mapping_index = headings.index("Legacy to Modern Mapping")
    create_index = headings.index("Creating New Project")
    add_index = headings.index("Adding Data to Project")

    assert mapping_index < create_index < add_index


def test_demo_notebook_defines_local_legacy_workflow_helpers():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    code_sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]

    assert any("def run_create_new_project_section(" in source for source in code_sources)
    assert any("def run_add_data_to_project_section(" in source for source in code_sources)


def test_demo_notebook_removes_single_discharge_demo_cell():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    code_sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]

    assert not any(
        'example = DEMO_CONFIG["example_stations"]["discharge"]' in source
        and 'payload = get_usgs_timeseries(' in source
        for source in code_sources
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_contains_legacy_workflow_sections tests/test_usgs_waterdata_demo.py::test_demo_notebook_orders_legacy_sections_after_mapping tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_legacy_workflow_helpers tests/test_usgs_waterdata_demo.py::test_demo_notebook_removes_single_discharge_demo_cell -v`
Expected: FAIL because the current notebook is not yet reorganized into the required section order and still reflects the single-discharge demo layout

- [ ] **Step 3: Replace the discharge-only demo structure with three separate markdown cells and one code cell per notebook-local helper**

```markdown
## Legacy to Modern Mapping

## Creating New Project

## Adding Data to Project
```

```python
from IPython.display import display

def run_create_new_project_section(bbox, workflow_types):
    return get_usgs_stations_in_bbox(bbox, workflow_types)
```

```python
def run_add_data_to_project_section(example_stations, output_dir, date_range):
    results = {}
    for workflow_type, station_config in example_stations.items():
        results[workflow_type] = {
            "payload": get_usgs_timeseries(
                station_config["station_id"],
                workflow_type,
                output_dir,
                parameter_code=station_config["parameter_code"],
                date_range=date_range,
            )
        }
    return results
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_contains_legacy_workflow_sections tests/test_usgs_waterdata_demo.py::test_demo_notebook_orders_legacy_sections_after_mapping tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_legacy_workflow_helpers tests/test_usgs_waterdata_demo.py::test_demo_notebook_removes_single_discharge_demo_cell -v`
Expected: PASS

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 2: Add Failing Tests for Notebook-Local Workflow Behavior

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write a test utility that extracts notebook helper source**

```python
def _load_notebook_helper_namespace():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    helper_sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and (
            "def run_create_new_project_section(" in "".join(cell.get("source", []))
            or "def run_add_data_to_project_section(" in "".join(cell.get("source", []))
        )
    ]
    namespace = {
        "DEMO_CONFIG": DEMO_CONFIG,
        "format_artifact_messages": format_artifact_messages,
        "get_usgs_stations_in_bbox": get_usgs_stations_in_bbox,
        "get_usgs_timeseries": get_usgs_timeseries,
        "pd": pd,
    }
    exec("\n\n".join(helper_sources), namespace)
    return namespace
```

- [ ] **Step 2: Write the failing create-section behavior test**

```python
def test_run_create_new_project_section_queries_three_workflows_without_exports(monkeypatch):
    namespace = _load_notebook_helper_namespace()
    captured = {}

    def fake_get_usgs_stations_in_bbox(bbox, data_types):
        captured["bbox"] = bbox
        captured["data_types"] = data_types
        return {name: pd.DataFrame([{"monitoring_location_id": f"{name}-1"}]) for name in data_types}

    namespace["get_usgs_stations_in_bbox"] = fake_get_usgs_stations_in_bbox

    result = namespace["run_create_new_project_section"](
        DEMO_CONFIG["bbox"],
        ["discharge", "gw_daily", "gw_periodic"],
    )

    assert list(captured["data_types"]) == ["discharge", "gw_daily", "gw_periodic"]
    assert set(result) == {"discharge", "gw_daily", "gw_periodic"}
```

- [ ] **Step 3: Write the failing add-section loop and partial-failure test**

```python
def test_run_add_data_to_project_section_loops_once_per_workflow_and_continues_after_failure():
    namespace = _load_notebook_helper_namespace()
    calls = []

    def fake_get_usgs_timeseries(station_id, workflow_type, output_dir, parameter_code=None, date_range=None):
        calls.append((station_id, workflow_type, parameter_code, date_range))
        if workflow_type == "gw_daily":
            raise RuntimeError("gw_daily failed")
        return {
            "frame": pd.DataFrame([{"value": 1.0}]),
            "records": [{"value": 1.0}],
            "files": {},
            "metadata": {},
        }

    namespace["get_usgs_timeseries"] = fake_get_usgs_timeseries
    namespace["format_artifact_messages"] = lambda files: ["ok"]

    result = namespace["run_add_data_to_project_section"](
        DEMO_CONFIG["example_stations"],
        ROOT / DEMO_CONFIG["output_dir"],
        DEMO_CONFIG["date_range"],
    )

    assert [workflow_type for _, workflow_type, _, _ in calls] == [
        "discharge",
        "gw_daily",
        "gw_periodic",
    ]
    assert result["gw_daily"]["error"] == "gw_daily failed"
    assert "payload" in result["discharge"]
    assert "payload" in result["gw_periodic"]
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_run_create_new_project_section_queries_three_workflows_without_exports tests/test_usgs_waterdata_demo.py::test_run_add_data_to_project_section_loops_once_per_workflow_and_continues_after_failure -v`
Expected: FAIL because the notebook-local helpers do not yet implement the required orchestration and per-workflow error handling

- [ ] **Step 5: Implement the notebook-local helper behavior**

```python
def run_create_new_project_section(bbox, workflow_types):
    return get_usgs_stations_in_bbox(bbox, workflow_types)


def run_add_data_to_project_section(example_stations, output_dir, date_range):
    results = {}
    for workflow_type, station_config in example_stations.items():
        try:
            payload = get_usgs_timeseries(
                station_config["station_id"],
                workflow_type,
                output_dir,
                parameter_code=station_config["parameter_code"],
                date_range=date_range,
            )
            results[workflow_type] = {
                "payload": payload,
                "artifact_messages": format_artifact_messages(payload["files"]),
                "error": None,
            }
        except Exception as exc:
            results[workflow_type] = {
                "payload": None,
                "artifact_messages": [],
                "error": str(exc),
            }
    return results
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_run_create_new_project_section_queries_three_workflows_without_exports tests/test_usgs_waterdata_demo.py::test_run_add_data_to_project_section_loops_once_per_workflow_and_continues_after_failure -v`
Expected: PASS

- [ ] **Step 7: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 3: Render the Two Legacy Sections in the Notebook

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write the failing notebook-render tests**

```python
def test_demo_notebook_create_section_uses_station_discovery_only():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    code_sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]

    create_section_source = next(source for source in code_sources if "run_create_new_project_section" in source)
    assert "get_usgs_stations_in_bbox" in create_section_source
    assert "get_usgs_timeseries" not in create_section_source
    assert "output_dir" not in create_section_source
    assert "format_artifact_messages" not in create_section_source
    assert "export_timeseries_artifacts" not in create_section_source


def test_demo_notebook_add_section_loops_all_three_workflows():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    code_sources = [
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]

    add_helper_source = next(
        source for source in code_sources if "def run_add_data_to_project_section(" in source
    )
    add_render_source = next(
        source
        for source in code_sources
        if 'timeseries_results = run_add_data_to_project_section(' in source
    )

    assert 'for workflow_type, station_config in example_stations.items()' in add_helper_source
    assert 'print(f"{workflow_type} json:' in add_render_source
    assert 'print(f"{workflow_type} csv:' in add_render_source
    assert (
        'print(f"{workflow_type} parquet:' in add_render_source
        or 'print(f"{workflow_type} warning:' in add_render_source
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_section_uses_station_discovery_only tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_section_loops_all_three_workflows -v`
Expected: FAIL until the notebook cells are reorganized around the two legacy sections

- [ ] **Step 3: Update the notebook cells to render the two sections**

```python
# Creating New Project
print("Creating New Project")
station_results = run_create_new_project_section(
    DEMO_CONFIG["bbox"],
    ["discharge", "gw_daily", "gw_periodic"],
)
for workflow_type, frame in station_results.items():
    print(f"{workflow_type}: {len(frame)} stations")
    display(frame.head())


# Adding Data to Project
print("Adding Data to Project")
timeseries_results = run_add_data_to_project_section(
    DEMO_CONFIG["example_stations"],
    ROOT / DEMO_CONFIG["output_dir"],
    DEMO_CONFIG["date_range"],
)
for workflow_type, result in timeseries_results.items():
    print(workflow_type)
    if result["error"]:
        print(f"{workflow_type} warning: {result['error']}")
    else:
        display(result["payload"]["frame"].head())
        files = result["payload"]["files"]
        if not files:
            print(f"{workflow_type} warning: No artifacts written")
        elif files["parquet"] is None:
            print(f"{workflow_type} json: {files['json']}")
            print(f"{workflow_type} csv: {files['csv']}")
            print(f"{workflow_type} warning: {files['parquet_error']}")
        else:
            print(f"{workflow_type} json: {files['json']}")
            print(f"{workflow_type} csv: {files['csv']}")
            print(f"{workflow_type} parquet: {files['parquet']}")
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_section_uses_station_discovery_only tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_section_loops_all_three_workflows -v`
Expected: PASS

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 4: Verify Executed Notebook Output for All Three Workflows

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Add a final notebook-output inspection test helper**

```python
def _collect_notebook_text_outputs():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    outputs = []
    for cell in notebook["cells"]:
        for output in cell.get("outputs", []):
            if "text" in output:
                outputs.append("".join(output["text"]))
            elif "data" in output and "text/plain" in output["data"]:
                outputs.append("".join(output["data"]["text/plain"]))
    return "\n".join(outputs)
```

- [ ] **Step 2: Add the executed-notebook output assertion**

```python
def test_executed_demo_notebook_shows_both_sections_and_all_workflows():
    import re

    output_text = _collect_notebook_text_outputs()

    assert "Creating New Project" in output_text
    assert "Adding Data to Project" in output_text
    assert "discharge" in output_text
    assert "gw_daily" in output_text
    assert "gw_periodic" in output_text
    assert (
        re.search(r"discharge json: .*\\.json", output_text)
        and re.search(r"discharge csv: .*\\.csv", output_text)
        and (
            re.search(r"discharge parquet: .*\\.parquet", output_text)
            or "discharge warning:" in output_text
        )
    )
    assert (
        re.search(r"gw_daily json: .*\\.json", output_text)
        and re.search(r"gw_daily csv: .*\\.csv", output_text)
        and (
            re.search(r"gw_daily parquet: .*\\.parquet", output_text)
            or "gw_daily warning:" in output_text
        )
    )
    assert (
        re.search(r"gw_periodic json: .*\\.json", output_text)
        and re.search(r"gw_periodic csv: .*\\.csv", output_text)
        and (
            re.search(r"gw_periodic parquet: .*\\.parquet", output_text)
            or "gw_periodic warning:" in output_text
        )
    )
```

- [ ] **Step 3: Run the test before notebook execution to verify it fails if outputs are stale**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_executed_demo_notebook_shows_both_sections_and_all_workflows -v`
Expected: FAIL until the notebook has been re-executed with the new section structure

- [ ] **Step 4: Execute the notebook end to end**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter --with pandas --with dataretrieval --with pyarrow jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`
Expected: notebook executes successfully and writes fresh outputs for the `Creating New Project` and `Adding Data to Project` section cells

- [ ] **Step 5: Run the full demo test file**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py -v`
Expected: PASS

- [ ] **Step 6: Inspect generated outputs**

```text
Check outputs/usgs_waterdata_demo for per-workflow JSON/CSV/parquet artifacts from the Add Data to Project section.
```

- [ ] **Step 7: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```
