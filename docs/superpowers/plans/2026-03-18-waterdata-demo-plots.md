# Waterdata Demo Plots Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a simple interactive matplotlib plotting section to the USGS waterdata demo notebook so users can switch between the generated `discharge`, `gw_daily`, and `gw_periodic` outputs with a single widget.

**Architecture:** Keep the plotting logic notebook-first, alongside the existing notebook-owned `waterdata` demo functions. Reuse `add_data_results` rather than introducing a second retrieval path, and keep `helpers/` unchanged except for any dependency-facing support already in place. Treat `ipywidgets` as required for this demo path.

**Tech Stack:** Python, Jupyter Notebook, `pandas`, `matplotlib`, `ipywidgets`, `pytest`, `uv`

---

## File Map

- [`notebooks/usgs_waterdata_demo.ipynb`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb)
  Responsibility: import plotting dependencies, add the `Plot Generated Outputs` section, define notebook-local plot helpers, and render the widget using `add_data_results`.
- [`tests/test_usgs_waterdata_demo.py`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py)
  Responsibility: verify the notebook imports plotting libraries, defines local plot helpers, includes the new section, and uses `add_data_results` to render the plot selector.
- [`requirements.txt`](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/requirements.txt)
  Responsibility: include `matplotlib` and `ipywidgets` alongside the existing notebook demo dependencies.

### Task 1: Add Failing Tests for Notebook Plotting

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Write failing tests for plotting imports, section headings, and helper names**

```python
def test_demo_notebook_imports_plotting_dependencies():
    sources = get_demo_notebook_sources("code")

    assert any("import matplotlib.pyplot as plt" in source for source in sources)
    assert any("import ipywidgets as widgets" in source for source in sources)


def test_demo_notebook_contains_plot_generated_outputs_section():
    sources = get_demo_notebook_sources("markdown")

    assert any("Plot Generated Outputs" in source for source in sources)


def test_demo_notebook_defines_local_plot_helpers():
    sources = get_demo_notebook_sources("code")

    assert any("def _prepare_plot_frame(" in source for source in sources)
    assert any("def plot_generated_output(" in source for source in sources)
    assert any("def render_plot_selector(" in source for source in sources)
```

- [ ] **Step 2: Write a failing render-cell test that asserts plotting uses `add_data_results`**

```python
def test_demo_notebook_plot_render_uses_generated_results():
    source = "".join(get_demo_notebook_cell("plot-render").get("source", []))

    assert "render_plot_selector(add_data_results)" in source
```

- [ ] **Step 3: Write failing notebook-helper tests for plot preparation and plotting**

```python
def test_notebook_prepare_plot_frame_parses_time_and_sorts():
    payload = {
        "frame": pd.DataFrame(
            [
                {"time": 2000, "value": 2.0},
                {"time": 1000, "value": 1.0},
            ]
        )
    }
    prepare = load_demo_notebook_function("_prepare_plot_frame")

    frame = prepare(payload)

    assert str(frame["time"].dtype).startswith("datetime64")
    assert frame["value"].tolist() == [1.0, 2.0]


def test_notebook_plot_generated_output_uses_selected_workflow(monkeypatch):
    calls = {"plot": []}

    class FakeAxis:
        def plot(self, x, y, marker=None):
            calls["plot"].append((list(y), marker))
        def set_title(self, value): calls["title"] = value
        def set_xlabel(self, value): calls["xlabel"] = value
        def set_ylabel(self, value): calls["ylabel"] = value
        def grid(self, value): calls["grid"] = value

    class FakeFigure:
        pass

    def fake_subplots(*args, **kwargs):
        return FakeFigure(), FakeAxis()

    plot_generated_output = load_demo_notebook_function(
        "plot_generated_output",
        {
            "_prepare_plot_frame": lambda payload: payload["frame"],
            "plt": SimpleNamespace(subplots=fake_subplots, show=lambda: None),
        },
    )

    add_data_results = {
        "discharge": {
            "payload": {
                "frame": pd.DataFrame(
                    [{"time": pd.Timestamp("2020-01-01"), "value": 1.0, "unit_of_measure": "ft^3/s"}]
                )
            },
            "error": None,
        }
    }

    plot_generated_output("discharge", add_data_results)

    assert calls["plot"] == [([1.0], "o")]
    assert "Discharge" in calls["title"]
```

- [ ] **Step 4: Run the targeted plotting tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_imports_plotting_dependencies tests/test_usgs_waterdata_demo.py::test_demo_notebook_contains_plot_generated_outputs_section tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_plot_helpers tests/test_usgs_waterdata_demo.py::test_demo_notebook_plot_render_uses_generated_results tests/test_usgs_waterdata_demo.py::test_notebook_prepare_plot_frame_parses_time_and_sorts tests/test_usgs_waterdata_demo.py::test_notebook_plot_generated_output_uses_selected_workflow -v`

Expected: FAIL because the notebook does not yet import plotting libraries, define plot helpers, or render the plotting section.

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 2: Implement Notebook Plot Helpers and Interactive Section

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Extend the notebook imports with plotting dependencies**

Add notebook imports:

```python
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import clear_output, display
```

- [ ] **Step 2: Add the new markdown section after `Adding Data to Project`**

Add:

```markdown
## Plot Generated Outputs

This section plots the same generated outputs created above, with a simple selector for switching between workflow types.
```

- [ ] **Step 3: Add the plot-preparation helper**

```python
def _prepare_plot_frame(payload):
    frame = payload["frame"].copy()
    frame["time"] = pd.to_datetime(frame["time"], unit="ms", errors="coerce")
    frame = frame.dropna(subset=["time", "value"]).sort_values("time").reset_index(drop=True)
    return frame
```

- [ ] **Step 4: Add the selected-workflow plotting helper**

```python
def plot_generated_output(workflow_type, add_data_results):
    result = add_data_results[workflow_type]
    if result["error"] or result["payload"] is None:
        print(f"Warning: no plot available for {workflow_type}")
        return

    frame = _prepare_plot_frame(result["payload"])
    if frame.empty:
        print(f"No rows available to plot for {workflow_type}")
        return

    unit = frame["unit_of_measure"].dropna().iloc[0] if "unit_of_measure" in frame else None
    station_id = frame["station_id"].dropna().iloc[0] if "station_id" in frame else None

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(frame["time"], frame["value"], marker="o")
    ax.set_title(f"{workflow_type.replace('_', ' ').title()} ({station_id})")
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Value ({unit})" if unit else "Value")
    ax.grid(True)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()
```

- [ ] **Step 5: Add the widget renderer and render cell**

```python
def render_plot_selector(add_data_results):
    dropdown = widgets.Dropdown(
        options=["discharge", "gw_daily", "gw_periodic"],
        value="discharge",
        description="Workflow:",
    )
    output = widgets.Output()

    def _render(change=None):
        with output:
            clear_output(wait=True)
            plot_generated_output(dropdown.value, add_data_results)

    dropdown.observe(_render, names="value")
    _render()
    display(widgets.VBox([dropdown, output]))


render_plot_selector(add_data_results)
```

- [ ] **Step 6: Run the targeted plotting tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_imports_plotting_dependencies tests/test_usgs_waterdata_demo.py::test_demo_notebook_contains_plot_generated_outputs_section tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_local_plot_helpers tests/test_usgs_waterdata_demo.py::test_demo_notebook_plot_render_uses_generated_results tests/test_usgs_waterdata_demo.py::test_notebook_prepare_plot_frame_parses_time_and_sorts tests/test_usgs_waterdata_demo.py::test_notebook_plot_generated_output_uses_selected_workflow -v`

Expected: PASS

- [ ] **Step 7: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 3: Update Dependencies and Verify the Executed Notebook

**Files:**
- Modify: `requirements.txt`
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Add plotting dependencies to `requirements.txt`**

Append:

```text
matplotlib
ipywidgets
```

- [ ] **Step 2: Execute the notebook with plotting dependencies**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter --with pandas --with matplotlib --with ipywidgets --with dataretrieval --with pyarrow jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`

Expected: notebook executes successfully and writes the updated rendered cells.

- [ ] **Step 3: Run the full demo test file**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py -q`

Expected: PASS

- [ ] **Step 4: Inspect the executed notebook outputs and generated artifacts**

Check:

- the executed notebook includes the `Plot Generated Outputs` section
- the earlier `Creating New Project` and `Adding Data to Project` outputs still render
- the JSON, CSV, and parquet files in `outputs/usgs_waterdata_demo/` remain present for all three workflow types

- [ ] **Step 5: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```
