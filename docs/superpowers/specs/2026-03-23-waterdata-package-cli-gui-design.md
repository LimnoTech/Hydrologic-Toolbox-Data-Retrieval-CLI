# Water Data Package, CLI, and GUI Design

## Summary

Build a reusable Python package alongside the existing notebook and helper module without changing either of those current files. The package should support both legacy workflow sections, `Creating New Project` and `Adding Data to Project`, and expose them through a single app entrypoint that runs as a CLI when arguments are present and opens a small desktop GUI when launched without arguments. The package should copy and adapt the needed notebook logic and helper behavior into documented modules, while notebook widget rendering remains notebook-only.

## Goals

- Preserve the current notebook experience and section structure exactly as-is.
- Leave the existing notebook and `helpers/` files unchanged.
- Copy notebook workflow logic, minus widget rendering, into documented Python modules.
- Keep JSON, CSV, and parquet export for `Adding Data to Project`.
- Support both workflows from a packaged app.
- Make the project buildable into a Windows `.exe` with PyInstaller.

## Non-Goals

- Replacing the notebook as the primary demo artifact.
- Adding shapefile export.
- Automating Windows builds from the current macOS workspace.
- Migrating notebook widgets into the package or GUI.

## User-Facing Behavior

### Notebook

- The notebook keeps the same high-level setup and story.
- The notebook and existing helper module are not modified by this package work.
- The notebook still shows:
  - `Legacy to Modern Mapping`
  - `Creating New Project`
  - `Adding Data to Project`
  - notebook-only interactive widget rendering
- The notebook remains an independent demo artifact rather than becoming a wrapper over the package.

### CLI Mode

- The packaged app runs in CLI mode when arguments are provided.
- It exposes two commands:
  - `create-new-project`
  - `add-data`
- `create-new-project` accepts bounding box inputs and workflow selection, then prints station summaries and preview-friendly output.
- `add-data` accepts workflow type, station id, parameter code, date range, and output directory, then writes JSON, CSV, and parquet.

### GUI Mode

- The packaged app opens a small desktop GUI when launched without arguments.
- The GUI uses `tkinter`.
- The GUI provides two simple workflow entry areas:
  - `Creating New Project`
  - `Adding Data to Project`
- The GUI is utility-like and intentionally simple.

## Package Structure

Use a `src/` layout and create a real package, for example:

```text
src/waterdata_toolbox_demo/
  __init__.py
  app.py
  cli.py
  config.py
  exports.py
  gui.py
  plotting.py
  station_discovery.py
  timeseries.py
```

### Module Responsibilities

#### `config.py`

- Holds `DEMO_CONFIG`, `LEGACY_CALLS`, and `NOTEBOOK_MAPPING_ROWS`.
- Copies the current configuration values so CLI and GUI defaults stay aligned with the notebook demo.

#### `station_discovery.py`

- Owns the `Creating New Project` workflow logic.
- Copies the notebook's station-discovery behavior into package functions.
- Includes:
  - `waterdata` discovery call orchestration
  - workflow-specific filtering logic
  - station normalization
  - GeoDataFrame conversion with CRS support

#### `timeseries.py`

- Owns the `Adding Data to Project` workflow logic.
- Copies the notebook's station-based retrieval behavior into package functions.
- Includes:
  - station id normalization
  - workflow-based retrieval branching
  - payload shaping for notebook, CLI, and GUI callers

#### `exports.py`

- Owns artifact export behavior.
- Includes:
  - JSON/CSV/parquet writing
  - export-safe geometry flattening
  - artifact message formatting

#### `plotting.py`

- Keeps shared non-widget plotting preparation logic only.
- Notebook widget rendering remains outside the package.

#### `cli.py`

- Owns argument parsing and command dispatch.
- Calls package workflow functions and prints concise results.

#### `gui.py`

- Owns the `tkinter` desktop interface.
- Calls the same package workflow functions used by the CLI.

#### `app.py`

- Single dual-mode entrypoint.
- Behavior:
  - arguments present -> CLI mode
  - no arguments -> GUI mode

## Workflow Integrity Requirements

### Creating New Project

- Preserve the current workflow-specific discovery behavior.
- Keep the distinction between:
  - `discharge`
  - `gw_daily`
  - `gw_periodic`
- Preserve the candidate-versus-qualifying filtering behavior because it is part of the workflow meaning, not just formatting.
- Preserve GeoPandas output with:
  - `geometry`
  - `gdf.crs`
  - `EPSG:4326`

### Adding Data to Project

- Preserve workflow branching:
  - `discharge` -> daily-values path
  - `gw_daily` -> daily-values path
  - `gw_periodic` -> field-measurements path
- Preserve output artifact generation:
  - JSON
  - CSV
  - parquet

## Notebook Preservation Rules

- Do not change the existing notebook.
- Do not change the existing `helpers/` module.
- Keep notebook widgets in the notebook only.
- Build the package as a sidecar implementation that copies the needed workflow logic and helper behavior.
- Keep the package behavior aligned with the notebook's current outputs and workflow meaning.

## Packaging and Build Design

### Python Packaging

- Add `pyproject.toml`.
- Use a `src/` layout for import hygiene.
- Add an app entrypoint for local package execution.

### PyInstaller

- Make the repo buildable into a Windows `.exe`.
- Document the build as Windows-only.
- Prefer one PyInstaller target aimed at `app.py`.
- Accept that a single executable may still open a console window even when GUI mode is used.
- Keep the design flexible so a later split into separate CLI and GUI executables is easy if needed.

## Testing Strategy

- Keep notebook-level tests that confirm the demo structure still works.
- Add package-level tests for:
  - station discovery behavior
  - GeoDataFrame shaping and CRS
  - time-series retrieval behavior
  - export behavior
  - CLI routing
  - GUI smoke-level construction
- Verify the package behavior against the existing notebook/helper expectations without modifying the notebook.

## Documentation Requirements

- Add docstrings to package modules and functions.
- Document how to:
  - run the package locally
  - launch GUI mode
  - run CLI mode
  - build the Windows `.exe` with PyInstaller

## Risks and Mitigations

- Single-entry CLI plus GUI behavior may be slightly awkward in PyInstaller.
  - Mitigation: keep a clean shared core so splitting executables later is easy.
- Copying logic instead of refactoring in place can create drift between the notebook and package over time.
  - Mitigation: keep package defaults and behavior aligned with the existing demo and add focused package tests around the copied workflow rules.
- GeoPandas and PyInstaller can be sensitive in frozen apps.
  - Mitigation: document Windows build steps clearly and keep imports organized by module responsibility.

## Acceptance Criteria

- The notebook and existing helper module remain unchanged.
- The package contains documented equivalents of the core workflow logic and non-widget helper behavior.
- The package supports both workflows.
- Running the shared app entrypoint with arguments uses CLI mode.
- Running the shared app entrypoint without arguments opens the GUI.
- `Adding Data to Project` still writes JSON, CSV, and parquet.
- The repo contains documented steps to build a Windows `.exe` with PyInstaller.
