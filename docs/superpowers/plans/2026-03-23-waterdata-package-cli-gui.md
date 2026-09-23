# Water Data Sidecar Package and Dual-Mode App Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a sidecar Python package that copies the current notebook/helper workflow logic into reusable modules, exposes both legacy workflows through one dual-mode app entrypoint, and is buildable into a Windows `.exe` with PyInstaller without changing the existing notebook or helper module.

**Architecture:** Create a new `src/waterdata_toolbox_demo/` package that mirrors the current demo logic in focused modules for config, station discovery, time series retrieval, exports, plotting preparation, CLI dispatch, GUI dispatch, and app routing. Keep [notebooks/usgs_waterdata_demo.ipynb](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/notebooks/usgs_waterdata_demo.ipynb) and [helpers/usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py) untouched, and validate the sidecar package against the current behavior rather than refactoring existing files.

**Tech Stack:** Python, `dataretrieval.waterdata`, pandas, GeoPandas, argparse, tkinter, pytest, PyInstaller, `pyproject.toml`

---

## File Map

- Create: `pyproject.toml`
- Create: `src/waterdata_toolbox_demo/__init__.py`
- Create: `src/waterdata_toolbox_demo/__main__.py`
- Create: `src/waterdata_toolbox_demo/app.py`
- Create: `src/waterdata_toolbox_demo/cli.py`
- Create: `src/waterdata_toolbox_demo/config.py`
- Create: `src/waterdata_toolbox_demo/exports.py`
- Create: `src/waterdata_toolbox_demo/gui.py`
- Create: `src/waterdata_toolbox_demo/plotting.py`
- Create: `src/waterdata_toolbox_demo/station_discovery.py`
- Create: `src/waterdata_toolbox_demo/timeseries.py`
- Create: `waterdata_toolbox_demo.spec`
- Create: `docs/waterdata-package-cli-gui.md`
- Create: `tests/test_waterdata_toolbox_demo_package.py`

## Execution Notes

- Do not modify `notebooks/usgs_waterdata_demo.ipynb`.
- Do not modify `helpers/usgs_waterdata_demo.py`.
- Do not make any commits; the user wants to handle commits personally.
- Keep the new package behavior aligned with the current notebook/helper outputs and workflow meaning.
- Treat `tests/test_waterdata_toolbox_demo_package.py` as a local validation file; the repo currently ignores the `tests/` directory.

### Task 1: Scaffold the sidecar package and app entrypoints

**Files:**
- Create: `pyproject.toml`
- Create: `src/waterdata_toolbox_demo/__init__.py`
- Create: `src/waterdata_toolbox_demo/__main__.py`
- Create: `src/waterdata_toolbox_demo/app.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing package import and app-routing tests**

Add local tests that assert:
- `import waterdata_toolbox_demo` succeeds
- `python -m waterdata_toolbox_demo --help` routes through CLI mode
- `app.main([])` routes to GUI bootstrap
- `app.main(["create-new-project"])` routes to CLI bootstrap

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "package_import or app_routes" -v`
Expected: FAIL because the package and entrypoint files do not exist yet.

- [ ] **Step 3: Add the minimal package scaffold**

Implement:
- `pyproject.toml` with project metadata, `src/` package discovery, and a console script entrypoint
- `__init__.py` with package version/module docstring
- `__main__.py` that calls `app.main()`
- `app.py` with dual-mode routing:
  - args present -> CLI
  - no args -> GUI

- [ ] **Step 4: Run the focused tests again**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "package_import or app_routes" -v`
Expected: PASS

### Task 2: Copy config, export, and plotting-prep support into the package

**Files:**
- Create: `src/waterdata_toolbox_demo/config.py`
- Create: `src/waterdata_toolbox_demo/exports.py`
- Create: `src/waterdata_toolbox_demo/plotting.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing support-layer tests**

Add tests that assert:
- package `DEMO_CONFIG`, `LEGACY_CALLS`, and `NOTEBOOK_MAPPING_ROWS` match the current helper values
- export logic writes JSON/CSV/parquet and reports parquet failures cleanly
- geometry flattening produces JSON-serializable output
- plot-frame preparation sorts by time and handles epoch, string, and datetime inputs

- [ ] **Step 2: Run the support-layer tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "config or export or plotting" -v`
Expected: FAIL because the modules and functions do not exist yet.

- [ ] **Step 3: Implement the copied support modules**

Copy and adapt behavior from [helpers/usgs_waterdata_demo.py](/Users/lludden/Documents/GitHub/WaterData%20ToolBox%20Demo/helpers/usgs_waterdata_demo.py):
- config constants into `config.py`
- artifact export, geometry flattening, and artifact message formatting into `exports.py`
- non-widget plot preparation into `plotting.py`

Keep docstrings on every public function.

- [ ] **Step 4: Re-run the support-layer tests**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "config or export or plotting" -v`
Expected: PASS

### Task 3: Add the sidecar `Creating New Project` workflow module

**Files:**
- Create: `src/waterdata_toolbox_demo/station_discovery.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing station-discovery tests**

Add tests that assert:
- discharge, `gw_daily`, and `gw_periodic` preserve their current workflow distinctions
- candidate-versus-qualifying filtering is preserved
- normalized station frames expose legacy preview columns
- returned station results are GeoDataFrames with `EPSG:4326`

- [ ] **Step 2: Run the station-discovery tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "station_discovery or geodataframe" -v`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement the copied station-discovery layer**

Copy and adapt behavior from:
- notebook `get_usgs_stations_in_bbox(...)`
- helper functions for:
  - warning filtering
  - coordinate extraction
  - GeoDataFrame conversion
  - `_normalize_station_frame(...)`

Expose a package-level workflow function that CLI and GUI can call directly.

- [ ] **Step 4: Re-run the station-discovery tests**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "station_discovery or geodataframe" -v`
Expected: PASS

### Task 4: Add the sidecar `Adding Data to Project` workflow module

**Files:**
- Create: `src/waterdata_toolbox_demo/timeseries.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing time-series tests**

Add tests that assert:
- station ids are normalized to the `USGS-...` form expected by `waterdata`
- `discharge` and `gw_daily` use the daily-values path
- `gw_periodic` uses the field-measurements path
- returned payloads include frame, records, files, and metadata
- exports still write JSON/CSV/parquet through the sidecar package

- [ ] **Step 2: Run the time-series tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "timeseries or station_id or payload" -v`
Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Implement the copied time-series layer**

Copy and adapt behavior from:
- notebook `get_usgs_timeseries(...)`
- helper warning-filter and station-id normalization behavior
- export integration through the new package `exports.py`

Expose one high-level function for a single workflow run and one orchestration helper for looping configured workflows.

- [ ] **Step 4: Re-run the time-series tests**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "timeseries or station_id or payload" -v`
Expected: PASS

### Task 5: Add the CLI front end

**Files:**
- Create: `src/waterdata_toolbox_demo/cli.py`
- Modify: `src/waterdata_toolbox_demo/app.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing CLI tests**

Add tests that assert:
- `create-new-project` parses bbox and workflow arguments
- `add-data` parses workflow, station id, parameter code, date range, and output directory
- CLI mode prints station summaries for create-project
- CLI mode prints artifact paths for add-data

- [ ] **Step 2: Run the CLI tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "cli or argparse" -v`
Expected: FAIL because the CLI module does not exist yet.

- [ ] **Step 3: Implement the CLI layer**

Implement:
- `argparse` subcommands for `create-new-project` and `add-data`
- default values sourced from package config
- concise console output that mirrors the notebook’s meaning without widget display code

- [ ] **Step 4: Re-run the CLI tests**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "cli or argparse" -v`
Expected: PASS

### Task 6: Add the small desktop GUI front end

**Files:**
- Create: `src/waterdata_toolbox_demo/gui.py`
- Modify: `src/waterdata_toolbox_demo/app.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Write the failing GUI smoke tests**

Add tests that assert:
- GUI bootstrap can construct the application without starting the full event loop
- the GUI exposes both workflow sections
- create-project actions call the station-discovery package function
- add-data actions call the time-series package function

- [ ] **Step 2: Run the GUI smoke tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "gui or tkinter" -v`
Expected: FAIL because the GUI module does not exist yet.

- [ ] **Step 3: Implement the GUI layer**

Implement a small `tkinter` app with:
- one workflow area for `Creating New Project`
- one workflow area for `Adding Data to Project`
- simple entry widgets, action buttons, and text output areas
- no notebook widget code copied into the GUI

- [ ] **Step 4: Re-run the GUI smoke tests**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "gui or tkinter" -v`
Expected: PASS

### Task 7: Add PyInstaller build assets and user docs

**Files:**
- Create: `waterdata_toolbox_demo.spec`
- Create: `docs/waterdata-package-cli-gui.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: Write the failing documentation/build expectation tests**

Add tests that assert:
- the repo includes a PyInstaller spec targeting the shared app entrypoint
- the docs include:
  - local package run instructions
  - CLI examples
  - GUI launch instructions
  - Windows-only PyInstaller build steps

- [ ] **Step 2: Run the documentation/build tests to verify they fail**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "pyinstaller or build_docs" -v`
Expected: FAIL because the spec and docs do not exist yet.

- [ ] **Step 3: Implement build assets and docs**

Add:
- a PyInstaller spec for the shared `app.py` entrypoint
- a short docs page covering package usage and Windows build steps
- any small `pyproject.toml` updates needed for package entrypoints

- [ ] **Step 4: Re-run the documentation/build tests**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "pyinstaller or build_docs" -v`
Expected: PASS

### Task 8: Run full local verification and confirm untouched existing surfaces

**Files:**
- Verify only: `notebooks/usgs_waterdata_demo.ipynb`
- Verify only: `helpers/usgs_waterdata_demo.py`
- Verify only: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Run the full local package test file**

Run: `python -m pytest tests/test_waterdata_toolbox_demo_package.py -q`
Expected: PASS

- [ ] **Step 2: Run package CLI smoke commands**

Run:
- `python -m waterdata_toolbox_demo create-new-project --workflow-type discharge`
- `python -m waterdata_toolbox_demo add-data --workflow-type discharge`

Expected:
- create-project prints a station summary
- add-data writes JSON/CSV/parquet and prints their paths

- [ ] **Step 3: Verify the existing notebook and helper module were not changed**

Run: `git diff -- notebooks/usgs_waterdata_demo.ipynb helpers/usgs_waterdata_demo.py`
Expected: no output

- [ ] **Step 4: Verify package files are the only new tracked implementation surface**

Run: `git status --short`
Expected:
- new package files
- new docs/spec files
- optional local ignored test files
- no edits to the notebook or helper module

- [ ] **Step 5: Stop before any commit**

Do not commit. Hand the workspace back to the user for review and any commit they want to create themselves.
