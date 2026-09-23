# Create Project GeoPandas Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `Creating New Project` use GeoPandas-backed bbox station results with visible CRS/geometry support while keeping the station widget in that section and preserving JSON/CSV/parquet export in `Adding Data to Project`.

**Architecture:** Keep the notebook responsible for the visible `dataretrieval.waterdata` calls and the two legacy workflow sections. Extend `helpers/usgs_waterdata_demo.py` so station normalization produces `GeoDataFrame` results that carry `geometry` and `crs`, while the notebook render cells keep the familiar previews and explicitly show the GIS-style metadata. Leave `Adding Data to Project` focused on time-series retrieval and output artifact writing.

**Tech Stack:** Python, Jupyter Notebook, `dataretrieval`, `pandas`, `geopandas`, `matplotlib`, `ipywidgets`, `pyarrow`, `pytest`, `uv`

---

## File Map

- [helpers/usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py)
  Responsibility: support helpers for station normalization, GeoDataFrame creation, create-project widget rendering, add-data plotting, and geometry-safe export flattening.
- [notebooks/usgs_waterdata_demo.ipynb](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb)
  Responsibility: visible `waterdata` retrieval calls, section markdown, create-project preview/render cells, add-data preview/render cells, and notebook-level explanation of `GeoDataFrame` plus `gdf.crs`.
- [tests/test_usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/tests/test_usgs_waterdata_demo.py)
  Responsibility: verify GeoPandas-backed create-project results, notebook section ownership, helper behavior, and retained add-data export behavior.
- [requirements.txt](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/requirements.txt)
  Responsibility: declare `geopandas` alongside the existing notebook/test dependencies.

### Task 1: Add Failing Coverage for GeoPandas Create-Project Behavior

**Files:**
- Modify: `tests/test_usgs_waterdata_demo.py`
- Modify: `requirements.txt`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Add a failing helper-level test that station normalization returns a GeoDataFrame with CRS**

```python
def test_normalize_station_frame_returns_geodataframe_with_crs():
    candidate_frame = pd.DataFrame(
        [
            {
                "monitoring_location_id": "USGS-1",
                "site_type_code": "ST",
                "location_name": "Surface One",
                "longitude": -82.1,
                "latitude": 32.0,
            }
        ]
    )
    qualifying_frame = pd.DataFrame([{"monitoring_location_id": "USGS-1"}])

    frame = _normalize_station_frame(candidate_frame, qualifying_frame, "discharge")

    assert type(frame).__name__ == "GeoDataFrame"
    assert str(frame.crs) == "EPSG:4326"
    assert "geometry" in frame.columns
```

- [ ] **Step 2: Add a failing notebook test that create-project render surfaces GeoDataFrame/CRS context while keeping previews**

```python
def test_demo_notebook_create_section_surfaces_geodataframe_context():
    source = "".join(get_demo_notebook_cell("create-section-render").get("source", []))

    assert "frame.crs" in source
    assert "type(frame).__name__" in source
    assert "display(" in source
```

- [ ] **Step 3: Add or update a failing test that add-data render still targets repo outputs and not bbox station previews**

```python
def test_demo_notebook_add_data_section_stays_timeseries_only():
    source = "".join(get_demo_notebook_cell("add-data-render").get("source", []))

    assert "run_add_data_to_project_section" in source
    assert "PROJECT_ROOT / DEMO_CONFIG[\"output_dir\"]" in source
    assert "render_station_discovery_selector" not in source
```

- [ ] **Step 4: Add `geopandas` to runtime dependencies**

```text
Append `geopandas` to requirements.txt so notebook execution and helper imports can rely on GeoPandas directly.
```

- [ ] **Step 5: Run the new targeted tests to verify they fail first**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas --with geopandas python -m pytest tests/test_usgs_waterdata_demo.py::test_normalize_station_frame_returns_geodataframe_with_crs tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_section_surfaces_geodataframe_context tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_data_section_stays_timeseries_only -v`

Expected: FAIL because station normalization still returns plain pandas output or the create-project render does not yet surface GeoPandas/CRS details.

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 2: Add GeoPandas Support to Station Discovery Helpers

**Files:**
- Modify: `helpers/usgs_waterdata_demo.py`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Import GeoPandas and add a helper that builds station GeoDataFrames**

Add a focused helper around the normalized station frame:

```python
import geopandas as gpd


def _to_station_geodataframe(frame):
    geometry = gpd.points_from_xy(frame["dec_long_va"], frame["dec_lat_va"], crs="EPSG:4326")
    return gpd.GeoDataFrame(frame.copy(), geometry=geometry, crs="EPSG:4326")
```

Keep the helper tolerant of missing numeric coordinates by coercing invalid lon/lat values to `NaN` before geometry creation.

- [ ] **Step 2: Update `_normalize_station_frame(...)` to return a GeoDataFrame**

Preserve the existing legacy preview columns:

```python
frame["site_no"] = ...
frame["station_nm"] = ...
frame["site_tp_cd"] = ...
frame["dec_lat_va"] = ...
frame["dec_long_va"] = ...
frame["state_cd"] = ...
frame["county_cd"] = ...
```

Then convert the normalized result into a `GeoDataFrame` with CRS `EPSG:4326` so callers can inspect `frame.crs` directly.

- [ ] **Step 3: Keep create-project plotting helpers compatible with GeoDataFrame inputs**

Adjust `_prepare_station_plot_frame(...)` and `plot_station_discovery_map(...)` only as needed so they continue reading `dec_long_va` and `dec_lat_va` from the GeoDataFrame without changing widget behavior.

- [ ] **Step 4: Extend geometry-safe export coverage if needed**

If GeoPandas introduces any new serialization edge cases, adapt `_prepare_frame_for_export(...)` so add-data exports still flatten geometry-bearing frames safely into JSON/CSV/parquet-friendly columns.

- [ ] **Step 5: Run the focused helper tests until they pass**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas --with geopandas python -m pytest tests/test_usgs_waterdata_demo.py::test_normalize_station_frame_returns_geodataframe_with_crs tests/test_usgs_waterdata_demo.py::test_prepare_station_plot_frame_keeps_numeric_lon_lat_rows tests/test_usgs_waterdata_demo.py::test_plot_station_discovery_map_uses_selected_workflow tests/test_usgs_waterdata_demo.py::test_export_writes_json_for_geopandas_style_frames -v`

Expected: PASS with GeoDataFrame station outputs, intact plotting, and intact geometry-safe export.

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 3: Update the Notebook Sections to Highlight GeoPandas in Creating New Project

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Modify: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Update create-project markdown to explain GeoDataFrame and CRS usage**

Add a short note in the `Creating New Project` section explaining that the bbox results are `GeoDataFrame`s with point geometry and `EPSG:4326`, and that inspecting `gdf.crs` is enough to demonstrate GIS-style metadata without writing shapefiles.

- [ ] **Step 2: Keep create-project previews and add explicit GeoPandas/CRS output**

Update the `create-section-render` cell so each workflow still prints the row count and displays the preview table, but now also shows GeoPandas context, for example:

```python
print(f"{workflow_type}: {len(frame)} stations")
print(type(frame).__name__)
print(frame.crs)
display(frame[available_columns + ["geometry"]].head())
```

Keep the preview compact and preserve the legacy-style columns the notebook already uses.

- [ ] **Step 3: Keep the station widget in `Creating New Project`**

Leave the `create-plot-render` cell as the home of:

```python
render_station_discovery_selector(create_section_results)
```

Do not move this widget or bbox station preview logic into the add-data cells.

- [ ] **Step 4: Keep add-data render focused on retrieval previews and artifact output**

Ensure the `add-data-render` cell continues to:

```python
add_data_results = run_add_data_to_project_section(
    DEMO_CONFIG["example_stations"],
    PROJECT_ROOT / DEMO_CONFIG["output_dir"],
    DEMO_CONFIG["date_range"],
)
```

It should still display the retrieved time-series previews and print JSON/CSV/parquet paths, with no create-project station widget logic mixed in.

- [ ] **Step 5: Run targeted notebook-structure tests**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas --with geopandas python -m pytest tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_section_surfaces_geodataframe_context tests/test_usgs_waterdata_demo.py::test_demo_notebook_render_create_section_uses_station_discovery_only tests/test_usgs_waterdata_demo.py::test_demo_notebook_create_project_plot_render_uses_create_results tests/test_usgs_waterdata_demo.py::test_demo_notebook_add_data_section_stays_timeseries_only tests/test_usgs_waterdata_demo.py::test_demo_notebook_render_add_data_section_loops_all_three_workflows -v`

Expected: PASS with create-project owning the GeoPandas station previews/widget and add-data owning the exported time-series workflow.

- [ ] **Step 6: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```

### Task 4: Re-verify the Executed Notebook and All Regression Coverage

**Files:**
- Modify: `notebooks/usgs_waterdata_demo.ipynb`
- Test: `tests/test_usgs_waterdata_demo.py`

- [ ] **Step 1: Run the full notebook test file with GeoPandas available**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with pytest --with pandas --with geopandas python -m pytest tests/test_usgs_waterdata_demo.py -q`

Expected: PASS for the full notebook/helper regression suite.

- [ ] **Step 2: Execute the notebook with GeoPandas included**

Run: `UV_CACHE_DIR=/tmp/uv-cache uv run --with jupyter --with pandas --with geopandas --with matplotlib --with ipywidgets --with dataretrieval --with pyarrow jupyter nbconvert --to notebook --execute --inplace notebooks/usgs_waterdata_demo.ipynb`

Expected: notebook executes successfully, writes the notebook in place, and continues the usual add-data artifacts in `outputs/usgs_waterdata_demo`.

- [ ] **Step 3: Confirm the saved notebook reflects the new create-project GeoPandas story**

Check the executed outputs to confirm:

```text
- create-project cells show all three workflow previews
- create-project output mentions GeoDataFrame and CRS
- create-project widget output is present
- add-data output still shows JSON/CSV/parquet paths
```

- [ ] **Step 4: Skip commit**

```text
Per user instruction, do not create a commit for this task.
```
