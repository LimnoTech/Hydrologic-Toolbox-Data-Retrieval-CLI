# Legacy Waterdata Workflow Alignment Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refocus the USGS waterdata demo notebook so both legacy workflow sections mirror the old sample-file themes, explain the legacy link differences, and provide a separate plot widget for `Creating New Project` and `Adding Data to Project`.

**Architecture:** Keep all `dataretrieval.waterdata` calls in [notebooks/usgs_waterdata_demo.ipynb](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb), with `helpers/usgs_waterdata_demo.py` limited to config and export support. Shape the notebook around the two legacy workflows from `data/`, add a bbox station-scatter widget to the create-project section, and keep a station time-series widget tied to the add-data exports. Treat the `data/` text files as read-only references for structure and explanation only.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval`, `pandas`, `matplotlib`, `ipywidgets`, `pytest`, `uv`

---

## File Map

- [notebooks/usgs_waterdata_demo.ipynb](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb)
  Responsibility: keep notebook-local `waterdata` calls, update legacy-link explanations, surface sample-shaped tables, add the `Creating New Project` station-scatter widget, and keep the `Adding Data to Project` time-series widget tied to `add_data_results`.
- [helpers/usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py)
  Responsibility: keep config, mapping rows, and export utilities support-only; update mapping metadata only if needed to better reflect the legacy link differences now explained in the notebook.
- [tests/test_usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py)
  Responsibility: verify notebook wording, helper boundaries, section-specific widget helpers, section render cells, and executed notebook outputs.
- `data/*.txt`
  Responsibility: reference-only examples of legacy output themes. Do not modify these files.

### Task 1: Add Failing Tests for Legacy-Link Notes and Dual Widget Coverage

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Add failing tests for the legacy link-difference notes**

```python
def test_demo_notebook_explains_legacy_new_project_link_differences():
    combined = "\n".join(get_demo_notebook_sources("markdown") + get_demo_notebook_sources("code"))

    assert "siteType=ST" in combined
    assert "siteType=GW" in combined
    assert "hasDataTypeCd=dv" in combined
    assert "parameterCd=00060" in combined
    assert "gw_periodic" in combined


def test_demo_notebook_explains_legacy_add_data_link_differences():
    combined = "\n".join(get_demo_notebook_sources("markdown") + get_demo_notebook_sources("code"))

    assert "get_daily" in combined
    assert "get_field_measurements" in combined
    assert "groundwater-level" in combined or "field-measurement" in combined
```

- [ ] **Step 2: Add failing tests for the new create-project plotting helpers and render cell**

```python
def test_demo_notebook_defines_create_project_plot_helpers():
    sources = get_demo_notebook_sources("code")

    assert any("def _prepare_station_plot_frame(" in source for source in sources)
    assert any("def plot_station_discovery_map(" in source for source in sources)
    assert any("def render_station_discovery_selector(" in source for source in sources)


def test_demo_notebook_create_project_plot_render_uses_create_results():
    source = "".join(get_demo_notebook_cell("create-plot-render").get("source", []))

    assert "render_station_discovery_selector(create_section_results)" in source
```

- [ ] **Step 3: Add failing tests that distinguish the add-data plot widget from the create-project widget**

```python
def test_demo_notebook_add_data_plot_render_uses_add_data_results():
    source = "".join(get_demo_notebook_cell("add-data-plot-render").get("source", []))

    assert "render_plot_selector(add_data_results)" in source


def test_demo_notebook_add_data_plot_lives_within_add_data_section():
    headings = get_demo_notebook_headings()

    assert "Creating New Project" in headings
    assert "Adding Data to Project" in headings


def test_demo_notebook_create_section_remains_display_only():
    source = "".join(get_demo_notebook_cell("create-section-render").get("source", []))

    assert "export_timeseries_artifacts" not in source
    assert "output_dir" not in source
```

- [ ] **Step 4: Add failing notebook-helper tests for the station-scatter behavior**

```python
def test_prepare_station_plot_frame_keeps_numeric_lon_lat_rows():
    prepare = load_demo_notebook_function("_prepare_station_plot_frame")
    frame = prepare(
        pd.DataFrame(
            [
                {"dec_long_va": "-82.1", "dec_lat_va": "32.0", "station_nm": "A"},
                {"dec_long_va": None, "dec_lat_va": "32.1", "station_nm": "B"},
            ]
        )
    )

    assert frame["station_nm"].tolist() == ["A"]


def test_plot_station_discovery_map_uses_selected_workflow():
    calls = {"scatter": []}

    class FakeAxis:
        def scatter(self, x, y):
            calls["scatter"].append((list(x), list(y)))
        def set_title(self, value): calls["title"] = value
        def set_xlabel(self, value): calls["xlabel"] = value
        def set_ylabel(self, value): calls["ylabel"] = value
        def grid(self, value): calls["grid"] = value

    def fake_subplots(*args, **kwargs):
        return object(), FakeAxis()

    plot_station_discovery_map = load_demo_notebook_function(
        "plot_station_discovery_map",
        {
            "_prepare_station_plot_frame": lambda frame: frame,
            "plt": SimpleNamespace(subplots=fake_subplots, show=lambda: None),
        },
    )

    create_section_results = {
        "discharge": pd.DataFrame([{"dec_long_va": -82.0, "dec_lat_va": 32.0}])
    }

    plot_station_discovery_map("discharge", create_section_results)

    assert calls["scatter"] == [([-82.0], [32.0])]
```

- [ ] **Step 5: Run the targeted tests to verify they fail**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_legacy_new_project_link_differences tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_legacy_add_data_link_differences tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_create_project_plot_helpers tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_project_plot_render_uses_create_results tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_data_plot_render_uses_add_data_results tests/test_usgs_waterdata_demo.py::test_prepare_station_plot_frame_keeps_numeric_lon_lat_rows tests/test_usgs_waterdata_demo.py::test_plot_station_discovery_map_uses_selected_workflow -v`

Expected: FAIL because the notebook does not yet expose the legacy-link notes and create-project widget in the tested form.

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 2: Implement the Legacy-Aligned Creating New Project Section

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Update the create-project notes to explain the legacy bbox link differences**

Add notebook text that explicitly maps the old station-discovery URLs to the modern notebook calls, including:

```text
discharge: siteType=ST, hasDataTypeCd=dv, parameterCd=00060
gw_daily: siteType=GW, hasDataTypeCd=dv
gw_periodic: broader bbox site search without the daily-value filter
```

- [ ] **Step 2: Make the station-discovery output look like the sample-file theme**

Keep or update the notebook-local station normalization so the rendered tables emphasize:

```python
[
    "site_no",
    "station_nm",
    "site_tp_cd",
    "dec_lat_va",
    "dec_long_va",
    "state_cd",
    "county_cd",
]
```

Use modern source columns where needed, but expose the legacy-style names in the displayed frame.

- [ ] **Step 3: Add the create-project plot helpers**

Add notebook-local helpers:

```python
def _prepare_station_plot_frame(frame):
    plot_frame = frame.copy()
    plot_frame["dec_long_va"] = pd.to_numeric(plot_frame["dec_long_va"], errors="coerce")
    plot_frame["dec_lat_va"] = pd.to_numeric(plot_frame["dec_lat_va"], errors="coerce")
    plot_frame = plot_frame.dropna(subset=["dec_long_va", "dec_lat_va"]).reset_index(drop=True)
    return plot_frame


def plot_station_discovery_map(workflow_type, create_section_results):
    frame = create_section_results[workflow_type]
    if frame.empty:
        print(f"No stations available to plot for {workflow_type}")
        return

    plot_frame = _prepare_station_plot_frame(frame)
    if plot_frame.empty:
        print(f"No mappable station coordinates available for {workflow_type}")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(plot_frame["dec_long_va"], plot_frame["dec_lat_va"])
    ax.set_title(f"{workflow_type.replace('_', ' ').title()} Station Discovery")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.grid(True)
    plt.show()
```

- [ ] **Step 4: Add the create-project widget renderer and render cell**

Add:

```python
def render_station_discovery_selector(create_section_results):
    dropdown = widgets.Dropdown(
        options=["discharge", "gw_daily", "gw_periodic"],
        value="discharge",
        description="Workflow:",
    )
    output = widgets.Output()

    def _render(change=None):
        with output:
            clear_output(wait=True)
            plot_station_discovery_map(dropdown.value, create_section_results)

    dropdown.observe(_render, names="value")
    _render()
    display(widgets.VBox([dropdown, output]))


render_station_discovery_selector(create_section_results)
```

Use a dedicated code cell id such as `create-plot-render` so the tests can target it.

- [ ] **Step 5: Run the create-project targeted tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_legacy_new_project_link_differences tests/test_usgs_waterdata_demo.py::test_demo_notebook_defines_create_project_plot_helpers tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_project_plot_render_uses_create_results tests/test_usgs_waterdata_demo.py::test_prepare_station_plot_frame_keeps_numeric_lon_lat_rows tests/test_usgs_waterdata_demo.py::test_plot_station_discovery_map_uses_selected_workflow -v`

Expected: PASS

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 3: Align the Adding Data to Project Section with the Legacy Samples

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Update notebook notes so the add-data section explicitly calls out the retrieval split**

Add notebook text that explains:

```text
discharge and gw_daily follow daily-values style station pulls
gw_periodic follows groundwater-level / field-measurement station retrieval
```

Reference the old link differences in the section notes, not just generic API descriptions.

- [ ] **Step 2: Keep the add-data preview shaped around the old sample theme**

Ensure the normalized add-data payloads and displayed preview frame expose the recurring sample columns:

```python
[
    "station_id",
    "time",
    "value",
    "qualifiers",
    "unit_of_measure",
]
```

Only include columns that are actually available, but prefer these names when rendering the preview.

- [ ] **Step 3: Keep the add-data time-series widget section-local**

Move or retitle the current plot cell structure so the add-data plot widget is clearly part of the `Adding Data to Project` workflow. Use or keep explicit helper names:

```python
def _prepare_plot_frame(payload): ...
def plot_generated_output(workflow_type, add_data_results): ...
def render_plot_selector(add_data_results): ...
```

Render it from a dedicated code cell id such as `add-data-plot-render`.

- [ ] **Step 4: Update helper metadata only if needed to better match the notebook’s legacy-link table**

If the mapping table needs clearer wording, update `NOTEBOOK_MAPPING_ROWS` in [helpers/usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py) so it stays aligned with the new notebook wording. Do not move retrieval logic back into helpers.

- [ ] **Step 5: Run the add-data targeted tests to verify they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_legacy_add_data_link_differences tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_data_plot_render_uses_add_data_results tests/test_usgs_waterdata_demo.py::test_demo_notebook_explains_waterdata_timeseries_usage tests/test_usgs_waterdata_demo.py::test_notebook_prepare_plot_frame_parses_time_and_sorts tests/test_usgs_waterdata_demo.py::test_notebook_plot_generated_output_uses_selected_workflow -v`

Expected: PASS after the add-data section text and render cell ids are aligned with the new section-local widget.

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 4: Execute the Notebook and Run the Full Demo Verification

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Execute the notebook end to end**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter --with pandas --with matplotlib --with ipywidgets --with dataretrieval --with pyarrow jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`

Expected: the notebook executes successfully and writes rendered outputs for both legacy sections and both widgets.

- [ ] **Step 2: Run the full waterdata demo test file**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas python -m pytest tests/test_usgs_waterdata_demo.py -q`

Expected: PASS

- [ ] **Step 3: Inspect the rendered notebook and output artifacts**

Check:

- `Creating New Project` displays the bbox station results for `discharge`, `gw_daily`, and `gw_periodic`
- `Creating New Project` includes the station-scatter widget
- `Creating New Project` writes no JSON, CSV, parquet, or `.rdb` artifacts
- `Adding Data to Project` displays the station-based outputs for all three workflow types
- `Adding Data to Project` includes the time-series widget
- `outputs/usgs_waterdata_demo/` still contains JSON, CSV, and parquet files for `discharge`, `gw_daily`, and `gw_periodic`
- no `.rdb` files are created

- [ ] **Step 4: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```
