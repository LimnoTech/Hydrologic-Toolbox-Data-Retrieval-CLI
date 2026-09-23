# CLI-Only Shapefile Workflows Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the packaged app to a CLI-only executable, make `create-new-project` write one shapefile per selected workflow, keep `add-data` on the custom CSV path, and document the reduced shapefile schema.

**Architecture:** Keep the existing workflow modules and GUI code in place, but remove GUI routing from the packaged app entrypoint so the `.exe` always behaves like a CLI. Replace `create-new-project` CSV exports with reduced-schema shapefile exports backed by the existing GeoDataFrame normalization logic, and introduce human-facing workflow flags that map into the current internal workflow names.

**Tech Stack:** Python, argparse, pandas, GeoPandas/Fiona, PyInstaller, pytest

---

## File Map

- Modify: `src/waterdata_toolbox_demo/app.py`
- Modify: `src/waterdata_toolbox_demo/cli.py`
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
- Create: `docs/create-new-project-shapefile-fields.md`
- Create: `docs/superpowers/specs/2026-04-27-cli-only-shapefile-workflows-design.md`
- Create: `docs/superpowers/plans/2026-04-27-cli-only-shapefile-workflows.md`

## Scope Notes

- Keep `src/waterdata_toolbox_demo/gui.py` and its logic in the repo.
- Do not route the packaged app entrypoint into the GUI path.
- Do not change the approved `add-data` CSV body/header contract.
- Use human-facing workflow flags:
  - `--discharge`
  - `--daily`
  - `--periodic`
- Map them internally to:
  - `discharge`
  - `gw_daily`
  - `gw_periodic`

### Task 1: Add failing tests for the CLI-only app contract

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Add a failing no-args app test**

Add a test like:

```python
def test_app_routes_to_cli_help_when_no_args(monkeypatch):
    from waterdata_toolbox_demo import app

    calls = []
    monkeypatch.setattr(app, "run_cli", lambda argv: calls.append(argv) or 0)
    monkeypatch.setattr(app, "run_gui", lambda: (_ for _ in ()).throw(AssertionError("GUI should not run")))

    result = app.main([])

    assert result == 0
    assert calls == [["--help"]]
```

- [ ] **Step 2: Add failing parser tests for the new workflow flags**

Add focused parser tests that assert:
- `create-new-project --discharge --daily` parses successfully
- `create-new-project` with no workflow flags fails
- `add-data --discharge` parses successfully
- `add-data --discharge --daily` fails

- [ ] **Step 3: Run the focused parser/app slice to verify it fails**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "app_routes or parser or cli_only" -v
```

Expected: FAIL because the current app still routes to GUI on no args and the parser still expects `--workflow-type`.

### Task 2: Add failing tests for shapefile create-project exports

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Replace the create-project CSV contract test with shapefile expectations**

Add a test that stubs station discovery dependencies and asserts:
- `run_create_new_project_section(..., ["discharge", "gw_periodic"], ...)` returns `files` with a `shp` key
- the output filenames are `discharge.shp` and `periodic.shp`
- the output directory also contains matching `.dbf`, `.shx`, and `.prj` sidecars

- [ ] **Step 2: Add a reduced-schema export test**

Add a focused test for the shapefile-export helper that reads the written layer back with GeoPandas and asserts the columns are exactly:

```python
["site_no", "loc_id", "stn_name", "site_tp", "state_cd", "county_cd", "lat", "lon", "agency_cd", "huc_code", "geometry"]
```

- [ ] **Step 3: Run the focused create-project/export slice to verify it fails**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "create_project or shapefile" -v
```

Expected: FAIL because the current branch still writes CSV files for create-project and has no shapefile reducer helper.

### Task 3: Implement the CLI-only runtime and new parser surface

**Files:**
- Modify: `src/waterdata_toolbox_demo/app.py`
- Modify: `src/waterdata_toolbox_demo/cli.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Change the app entrypoint to route no-arg launches to CLI help**

Update `app.main(...)` so:
- arguments present -> `run_cli(args)`
- no arguments -> `run_cli(["--help"])`
- `run_gui()` remains defined but unused by the packaged app path

- [ ] **Step 2: Add small CLI helpers for workflow-flag mapping**

In `cli.py`, add helpers such as:

```python
def _selected_create_workflows(args):
    mapping = [("discharge", args.discharge), ("gw_daily", args.daily), ("gw_periodic", args.periodic)]
    selected = [workflow for workflow, enabled in mapping if enabled]
    if not selected:
        raise SystemExit("at least one workflow flag is required")
    return selected
```

and:

```python
def _selected_add_workflow(args):
    selected = _selected_create_workflows(args)
    if len(selected) != 1:
        raise SystemExit("exactly one workflow flag is required for add-data")
    return selected[0]
```

- [ ] **Step 3: Replace `--workflow-type` arguments with the new flags**

Update `build_parser()` so:
- `create-new-project` gets optional `--bbox`, `--output-dir`, and three boolean workflow flags
- `add-data` gets `--discharge`, `--daily`, `--periodic`, `--station-id`, `--parameter-code`, `--start-date`, `--end-date`, `--output-dir`

- [ ] **Step 4: Update `run_cli()` to use the new workflow helpers**

Make sure:
- `create-new-project` uses `_selected_create_workflows(args)` and `Path(args.output_dir)`
- `add-data` uses `_selected_add_workflow(args)` and keeps the existing config-based defaults

- [ ] **Step 5: Run the parser/app test slice again**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "app_routes or parser or cli_only" -v
```

Expected: PASS

### Task 4: Implement reduced-schema shapefile exports for create-project

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Add a station-frame reducer for shapefile-safe columns**

In `exports.py`, add a helper that maps the normalized frame into:

```python
{
    "site_no": ...,
    "loc_id": ...,
    "stn_name": ...,
    "site_tp": ...,
    "state_cd": ...,
    "county_cd": ...,
    "lat": ...,
    "lon": ...,
    "agency_cd": ...,
    "huc_code": ...,
}
```

- [ ] **Step 2: Add a shapefile writer helper**

Implement a helper in `exports.py` that:
- accepts the normalized GeoDataFrame and output stem
- preserves EPSG:4326 geometry
- writes `driver="ESRI Shapefile"`
- returns a files mapping with the `.shp` path

- [ ] **Step 3: Swap `run_create_new_project_section()` to shapefile output**

In `station_discovery.py`, replace `export_station_artifacts(...)` with the new shapefile helper and map output stems:
- `discharge`
- `daily`
- `periodic`

- [ ] **Step 4: Keep `add-data` on the CSV path**

Confirm no `timeseries.py` behavior changes are needed beyond any import adjustments.

- [ ] **Step 5: Run the create-project/export slice again**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "create_project or shapefile or csv_only" -v
```

Expected: PASS

### Task 5: Document the shapefile field reductions and CLI-only packaging story

**Files:**
- Create: `docs/create-new-project-shapefile-fields.md`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the field-reduction note under `docs/`**

Document:
- the kept shapefile fields
- the excluded fields grouped by reason
- why shapefile limits require the reduction

- [ ] **Step 2: Rewrite the package doc around CLI-only usage**

Update the package doc so it says:
- the `.exe` is CLI-only
- no-arg launch prints help
- `create-new-project` writes shapefiles
- `add-data` writes CSV
- the GUI code remains in the repo but is not the packaged runtime path

- [ ] **Step 3: Update the doc test to assert the new messaging**

Check for:
- `CLI-only`
- `create-new-project`
- `discharge.shp`
- presence of the new docs note path
- absence of GUI-launch instructions in the packaged-app story

### Task 6: Run end-to-end verification

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Run the full focused package suite**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -v
```

Expected: PASS

- [ ] **Step 2: Smoke-test create-new-project**

Run:

```bash
/bin/zsh -lc "PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --output-dir dist/outputs/cli_shp_smoke"
```

Expected:
- command succeeds
- `dist/outputs/cli_shp_smoke/discharge.shp` exists with shapefile sidecars

- [ ] **Step 3: Smoke-test multi-workflow create-new-project**

Run:

```bash
/bin/zsh -lc "PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --daily --output-dir dist/outputs/cli_shp_smoke_multi"
```

Expected:
- `discharge.shp`
- `daily.shp`

- [ ] **Step 4: Smoke-test add-data**

Run:

```bash
/bin/zsh -lc "PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo add-data --discharge --station-id 02225500 --parameter-code 00060 --output-dir dist/outputs/cli_csv_smoke"
```

Expected:
- `dist/outputs/cli_csv_smoke/discharge_02225500.csv`
- no JSON/parquet companion files

- [ ] **Step 5: Leave work uncommitted until requested**

Do not commit or push unless the user explicitly asks.
