# Notebook Helper Support Refactor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move notebook support helpers into `helpers/usgs_waterdata_demo.py`, keep the live `waterdata` retrieval functions visible in the notebook, and add docstrings to every top-level notebook-defined function.

**Architecture:** Keep `notebooks/usgs_waterdata_demo.ipynb` responsible for workflow explanation, direct `waterdata` calls, and top-level section orchestration. Move support-only utilities into `helpers/usgs_waterdata_demo.py`, including station normalization, warning wrappers, plot-frame preparation, and widget rendering. Treat only top-level notebook functions as subject to the new docstring rule; nested widget callbacks do not need standalone docstring coverage.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval`, `pandas`, `matplotlib`, `ipywidgets`, `pytest`, `uv`

---

## File Map

- [helpers/usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py)
  Responsibility: config, mapping rows, export utilities, and the moved notebook support helpers:
  - `_call_station_discovery_with_filtered_datetime_warning`
  - `_extract_decimal_coordinate`
  - `_normalize_station_frame`
  - `_prepare_station_plot_frame`
  - `plot_station_discovery_map`
  - `render_station_discovery_selector`
  - `_normalize_monitoring_location_id`
  - `_call_waterdata_with_filtered_datetime_warning`
  - `_prepare_plot_frame`
  - `plot_generated_output`
  - `render_plot_selector`
- [notebooks/usgs_waterdata_demo.ipynb](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb)
  Responsibility: markdown explanations, direct `waterdata` service calls, top-level workflow functions, top-level render cells, and docstrings on every top-level notebook-defined function.
- [tests/test_usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py)
  Responsibility: verify helper ownership, notebook docstrings, helper behavior, notebook imports, and executed notebook outputs.

### Task 1: Add Failing Tests for Helper Ownership and Notebook Docstrings

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Add failing tests that the notebook imports support helpers instead of defining them locally**

```python
def test_demo_notebook_imports_support_helpers_from_helpers_module():
    sources = get_demo_notebook_sources("code")
    combined = "\n".join(sources)

    assert "from helpers.usgs_waterdata_demo import (" in combined
    assert "_normalize_station_frame" in combined
    assert "render_station_discovery_selector" in combined
    assert "render_plot_selector" in combined


def test_demo_notebook_no_longer_defines_moved_support_helpers_locally():
    sources = get_demo_notebook_sources("code")

    assert not any("def _normalize_station_frame(" in source for source in sources)
    assert not any("def _prepare_station_plot_frame(" in source for source in sources)
    assert not any("def render_station_discovery_selector(" in source for source in sources)
    assert not any("def _prepare_plot_frame(" in source for source in sources)
    assert not any("def render_plot_selector(" in source for source in sources)
```

- [ ] **Step 2: Add a failing test for top-level notebook function docstrings**

```python
def test_notebook_top_level_functions_have_docstrings():
    required = {
        "get_usgs_stations_in_bbox",
        "run_create_new_project_section",
        "get_usgs_timeseries",
        "run_add_data_to_project_section",
    }
    notebook = load_demo_notebook()
    function_nodes = {}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        module = ast.parse("".join(cell.get("source", [])))
        for node in module.body:
            if isinstance(node, ast.FunctionDef):
                function_nodes[node.name] = node

    for function_name in required:
        assert ast.get_docstring(function_nodes[function_name]), function_name
```

- [ ] **Step 3: Add failing tests for the moved helper behavior on the helper module surface**

```python
def test_helper_module_exports_moved_notebook_support_functions():
    import helpers.usgs_waterdata_demo as demo_helpers

    for name in [
        "_normalize_station_frame",
        "_prepare_station_plot_frame",
        "plot_station_discovery_map",
        "render_station_discovery_selector",
        "_prepare_plot_frame",
        "plot_generated_output",
        "render_plot_selector",
    ]:
        assert hasattr(demo_helpers, name), name
```

- [ ] **Step 4: Run the targeted ownership/docstring tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_imports_support_helpers_from_helpers_module tests/test_usgs_waterdata_demo.py::test_demo_notebook_no_longer_defines_moved_support_helpers_locally tests/test_usgs_waterdata_demo.py::test_notebook_top_level_functions_have_docstrings tests/test_usgs_waterdata_demo.py::test_helper_module_exports_moved_notebook_support_functions -v`

Expected: FAIL because the notebook still defines the support helpers locally and the helper module does not yet export them.

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 2: Move Notebook Support Helpers into `helpers/usgs_waterdata_demo.py`

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Add the moved station-discovery support helpers to the helper module**

Add helper implementations for:

```python
def _call_station_discovery_with_filtered_datetime_warning(function, **kwargs): ...
def _extract_decimal_coordinate(value, axis): ...
def _normalize_station_frame(candidate_frame, qualifying_frame, workflow_type): ...
def _prepare_station_plot_frame(frame): ...
def plot_station_discovery_map(workflow_type, create_section_results): ...
def render_station_discovery_selector(create_section_results): ...
```

Keep these functions generic around input frames and plotting state. They must not call `waterdata` on their own.

- [ ] **Step 2: Add the moved add-data support helpers to the helper module**

Add helper implementations for:

```python
def _normalize_monitoring_location_id(station_id): ...
def _call_waterdata_with_filtered_datetime_warning(function, **kwargs): ...
def _prepare_plot_frame(payload): ...
def plot_generated_output(workflow_type, add_data_results): ...
def render_plot_selector(add_data_results): ...
```

These helpers should preserve the current add-data widget behavior so the notebook render cells stay simple.

- [ ] **Step 3: Add or adapt direct helper-module tests for the moved behavior**

Convert the current notebook-helper tests to import from `helpers.usgs_waterdata_demo` where appropriate, for example:

```python
from helpers.usgs_waterdata_demo import _prepare_station_plot_frame


def test_prepare_station_plot_frame_keeps_numeric_lon_lat_rows():
    frame = _prepare_station_plot_frame(
        pd.DataFrame(
            [
                {"dec_long_va": "-82.1", "dec_lat_va": "32.0", "station_nm": "A"},
                {"dec_long_va": None, "dec_lat_va": "32.1", "station_nm": "B"},
            ]
        )
    )

    assert frame["station_nm"].tolist() == ["A"]
```

Apply the same move to the add-data plot helper coverage by rewriting the old notebook-scoped tests into helper-module tests such as:

```python
from helpers.usgs_waterdata_demo import _prepare_plot_frame, plot_generated_output


def test_helper_prepare_plot_frame_parses_time_and_sorts():
    payload = {
        "frame": pd.DataFrame(
            [
                {"time": 2000, "value": 2.0},
                {"time": 1000, "value": 1.0},
            ]
        )
    }

    frame = _prepare_plot_frame(payload)

    assert str(frame["time"].dtype).startswith("datetime64")
    assert frame["value"].tolist() == [1.0, 2.0]
```

- [ ] **Step 4: Run the moved-helper tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_helper_module_exports_moved_notebook_support_functions tests/test_usgs_waterdata_demo.py::test_prepare_station_plot_frame_keeps_numeric_lon_lat_rows tests/test_usgs_waterdata_demo.py::test_plot_station_discovery_map_uses_selected_workflow tests/test_usgs_waterdata_demo.py::test_helper_prepare_plot_frame_parses_time_and_sorts tests/test_usgs_waterdata_demo.py::test_helper_plot_generated_output_uses_selected_workflow -v`

Expected: PASS after the helper module owns the support behavior.

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 3: Refactor the Notebook to Use Imported Support Helpers and Add Docstrings

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Update the notebook imports to pull in the moved helper functions**

Extend the existing helper import block to include the moved support helpers:

```python
from helpers.usgs_waterdata_demo import (
    DEMO_CONFIG,
    NOTEBOOK_MAPPING_ROWS,
    _call_station_discovery_with_filtered_datetime_warning,
    _extract_decimal_coordinate,
    _normalize_station_frame,
    _normalize_monitoring_location_id,
    _call_waterdata_with_filtered_datetime_warning,
    render_station_discovery_selector,
    render_plot_selector,
    export_timeseries_artifacts,
    format_artifact_messages,
)
```

Adjust the exact import list to match the helper functions you keep as notebook dependencies.

- [ ] **Step 2: Remove the moved helper definitions from notebook cells**

Strip the notebook-local definitions for:

```python
_call_station_discovery_with_filtered_datetime_warning
_extract_decimal_coordinate
_normalize_station_frame
_prepare_station_plot_frame
plot_station_discovery_map
render_station_discovery_selector
_normalize_monitoring_location_id
_call_waterdata_with_filtered_datetime_warning
_prepare_plot_frame
plot_generated_output
render_plot_selector
```

Leave the top-level render cells intact, but make them call the imported helpers.

- [ ] **Step 3: Add docstrings to every remaining top-level notebook-defined function**

Add short docstrings to:

```python
def get_usgs_stations_in_bbox(...):
    """Retrieve workflow-specific stations inside a bounding box using waterdata."""


def run_create_new_project_section(...):
    """Run the legacy-style station discovery section for the requested workflows."""


def get_usgs_timeseries(...):
    """Retrieve and export workflow-specific time series for a selected station."""


def run_add_data_to_project_section(...):
    """Run the legacy-style add-data section for all configured example stations."""
```

If additional top-level notebook functions remain after the helper move, add docstrings to them too.

- [ ] **Step 4: Run the targeted notebook tests to verify the new ownership split**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_imports_support_helpers_from_helpers_module tests/test_usgs_waterdata_demo.py::test_demo_notebook_no_longer_defines_moved_support_helpers_locally tests/test_usgs_waterdata_demo.py::test_notebook_top_level_functions_have_docstrings tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_waterdata_retrieval_functions tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_project_plot_render_uses_create_results tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_data_plot_render_uses_add_data_results -v`

Expected: PASS

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 4: Re-Execute the Notebook and Run Full Verification

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Run the full notebook test file**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py -q`

Expected: PASS

- [ ] **Step 2: Execute the notebook end to end**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter --with pandas --with matplotlib --with ipywidgets --with dataretrieval --with pyarrow jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`

Expected: the notebook executes successfully and writes the refreshed render cells.

- [ ] **Step 3: Inspect the executed notebook and artifacts**

Check:

- the notebook still shows both legacy workflow sections
- `create-plot-render` still displays the station widget
- `add-data-plot-render` still displays the add-data widget
- only the add-data section writes JSON/CSV/parquet artifacts
- no repo-root bootstrap logic has been reintroduced

- [ ] **Step 4: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```
