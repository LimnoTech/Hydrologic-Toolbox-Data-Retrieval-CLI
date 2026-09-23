# Pure-Python Shapefile Writer Fix Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the packaged app's runtime dependency on Fiona/pyogrio/GDAL for shapefile writing by replacing the current GeoPandas `to_file()` path with a pure-Python writer.

**Architecture:** Keep the existing reduced-schema GeoDataFrame normalization and CLI behavior, but swap the final shapefile write step to `pyshp`. Write `.prj` and `.cpg` sidecars directly so the packaged `.exe` can export shapefiles using only Python-level dependencies.

**Tech Stack:** Python, GeoPandas, pyshp, PyInstaller, pytest

---

## File Map

- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
- Create: `docs/superpowers/specs/2026-04-27-pure-python-shapefile-writer-fix-design.md`
- Create: `docs/superpowers/plans/2026-04-27-pure-python-shapefile-writer-fix.md`

### Task 1: Add failing tests for the pure-Python writer path

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Replace shapefile inspection with `pyshp`**

Update the shapefile export test so it reads the written files with `shapefile.Reader(...)` instead of `GeoPandas.read_file(...)`.

- [ ] **Step 2: Add a sidecar-content assertion**

Assert:
- `.prj` exists and contains `WGS_1984`
- `.cpg` exists and contains `UTF-8`

- [ ] **Step 3: Run the focused shapefile slice and confirm it fails before the fix**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "shapefile" -v
```

Expected: FAIL until the runtime dependency and export path are updated.

### Task 2: Add the pure-Python dependency and replace the write path

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/waterdata_toolbox_demo/exports.py`

- [ ] **Step 1: Add `pyshp` to runtime dependencies**

Update `pyproject.toml` dependencies to include:

```toml
"pyshp",
```

- [ ] **Step 2: Install the dependency in the local environment**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pip install pyshp
```

- [ ] **Step 3: Replace `GeoDataFrame.to_file()` with `pyshp` writing**

Implement a helper in `exports.py` that:
- creates a point shapefile writer
- defines reduced-schema DBF fields explicitly
- writes point geometries from the GeoDataFrame geometry column
- writes matching DBF rows
- closes the writer

- [ ] **Step 4: Write `.prj` and `.cpg` sidecars manually**

Use:
- WGS84 `.prj` text
- `UTF-8` in `.cpg`

- [ ] **Step 5: Re-run the focused shapefile slice**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "shapefile" -v
```

Expected: PASS

### Task 3: Update docs and verify the failing Windows scenario is addressed

**Files:**
- Modify: `README.md`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Update docs wording**

Note that the packaged shapefile export uses a pure-Python writer and does not require Fiona/pyogrio/GDAL at runtime.

- [ ] **Step 2: Run the full package test file**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -v
```

Expected: PASS

- [ ] **Step 3: Re-run live CLI smoke tests**

Run:

```bash
/bin/zsh -lc "PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --output-dir dist/outputs/cli_shp_smoke"
/bin/zsh -lc "PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --daily --output-dir dist/outputs/cli_shp_smoke_multi"
```

Expected:
- shapefile sets are written successfully
- no Fiona/pyogrio import dependency is exercised during export

- [ ] **Step 4: Leave work uncommitted until requested**

Do not commit or push unless the user explicitly asks.
