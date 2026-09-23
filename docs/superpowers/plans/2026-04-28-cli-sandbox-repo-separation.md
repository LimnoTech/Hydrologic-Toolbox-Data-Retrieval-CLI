# CLI Sandbox Repo Separation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reshape the repo so the top-level product surface reflects only the active CLI app and `.exe` build path, while moving GUI code and other non-CLI materials into `sandbox/` and keeping `tests/` at repo root.

**Architecture:** Keep the active CLI package small and direct under `src/waterdata_toolbox_demo`, with `app.py`, `cli.py`, config, export, station-discovery, and timeseries logic remaining in place. Move GUI, plotting, helpers, notebooks, example data, and older product-facing docs under `sandbox/`, then clean up package metadata and build files so the active package no longer references GUI-first or legacy paths.

**Tech Stack:** Python packaging with setuptools, PyInstaller, pytest, filesystem moves

---

## File Map

- Modify: `src/waterdata_toolbox_demo/app.py`
  - remove GUI routing helpers from the active product surface
- Modify: `pyproject.toml`
  - update description and package readme path for CLI-only packaging
- Modify: `waterdata_toolbox_demo.spec`
  - remove GUI-specific packaging references
- Modify: `README.md`
  - keep root README product-facing and CLI-focused
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
  - update any doc/path expectations affected by moved files
- Move: `src/waterdata_toolbox_demo/gui.py`
  - to `sandbox/src/waterdata_toolbox_demo/gui.py`
- Move: `src/waterdata_toolbox_demo/plotting.py`
  - to `sandbox/src/waterdata_toolbox_demo/plotting.py`
- Move: `helpers/`
  - to `sandbox/helpers/`
- Move: `notebooks/`
  - to `sandbox/notebooks/`
- Move: `example_data/`
  - to `sandbox/example_data/`
- Move: `docs/waterdata-package-cli-gui.md`
  - to `sandbox/docs/waterdata-package-cli-gui.md`
- Optional move/update: additional legacy root/docs markdown files that are no longer the active CLI story

## Implementation Notes

- Do not touch gitignored/generated content as part of this cleanup.
- Keep `tests/` at repo root, even when tests cover moved or sandboxed content.
- Do not commit during execution unless the user explicitly asks.
- Prefer moving files rather than copying them so the active surface is clearly reduced.

## Task 1: Lock The New Repo Boundary With Failing Tests

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
- Reference: `src/waterdata_toolbox_demo/app.py`
- Reference: `pyproject.toml`
- Reference: `README.md`

- [ ] **Step 1: Add a failing test that the active package surface no longer includes GUI routing**

Add or update a test so it asserts the active app entrypoint no longer exposes or relies on `run_gui()` from `src/waterdata_toolbox_demo/app.py`.

Good assertions:

```python
from waterdata_toolbox_demo import app

assert not hasattr(app, "run_gui")
```

or an equivalent behavior-level check that proves the active app no longer imports GUI code.

- [ ] **Step 2: Add a failing packaging/doc path expectation**

Update the existing package/config test coverage so it asserts:

- `pyproject.toml` no longer describes the project as a CLI-and-GUI app
- the package `readme` path points to the active root `README.md` or another non-sandbox CLI-facing file
- the active root `README.md` remains present and CLI-focused

Expected initial result: FAIL because current metadata still references GUI wording and an old package-note path.

- [ ] **Step 3: Add a failing test for sandboxed legacy docs**

Add or update a test to assert:

- `sandbox/docs/waterdata-package-cli-gui.md` exists
- the old top-level `docs/waterdata-package-cli-gui.md` path is no longer the active expected package-doc location

- [ ] **Step 4: Run the focused package/config tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_packaging_config.py tests/test_waterdata_toolbox_demo_package.py -k "app or package or build or docs" -v
```

Expected: FAIL on the new repo-boundary assertions.

## Task 2: Move GUI And Sidecar Code Into `sandbox/`

**Files:**
- Move: `src/waterdata_toolbox_demo/gui.py`
- Move: `src/waterdata_toolbox_demo/plotting.py`
- Modify: `src/waterdata_toolbox_demo/app.py`
- Modify: `waterdata_toolbox_demo.spec`

- [ ] **Step 1: Move GUI module to sandbox**

Move:

```text
src/waterdata_toolbox_demo/gui.py
-> sandbox/src/waterdata_toolbox_demo/gui.py
```

Keep the file content intact unless an import path must be adjusted for the move.

- [ ] **Step 2: Move plotting helper module to sandbox**

Move:

```text
src/waterdata_toolbox_demo/plotting.py
-> sandbox/src/waterdata_toolbox_demo/plotting.py
```

This keeps non-CLI sidecar utilities out of the active package surface.

- [ ] **Step 3: Remove GUI routing from the active app entrypoint**

Edit `src/waterdata_toolbox_demo/app.py` so:

- `run_gui()` is removed
- no import of `waterdata_toolbox_demo.gui` remains
- `main()` stays CLI-only and still routes empty args to `--help`

The active entrypoint should remain small and straightforward.

- [ ] **Step 4: Remove GUI packaging references**

Edit `waterdata_toolbox_demo.spec` to remove GUI-specific hidden imports or packaging references such as:

- `waterdata_toolbox_demo.gui`

Only keep what the active CLI build actually needs.

- [ ] **Step 5: Run the focused app/build tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "app_routes or package_build_docs" -v
```

Expected: PASS for the GUI-removal boundary checks.

## Task 3: Move Legacy Project Material Into `sandbox/`

**Files:**
- Move: `helpers/`
- Move: `notebooks/`
- Move: `example_data/`
- Move: `docs/waterdata-package-cli-gui.md`
- Optional move: other old product-facing markdown files as approved during execution

- [ ] **Step 1: Move helper module directory**

Move:

```text
helpers/
-> sandbox/helpers/
```

Do not reorganize internal helper contents during this move.

- [ ] **Step 2: Move notebook directory**

Move:

```text
notebooks/
-> sandbox/notebooks/
```

Keep notebook outputs/checkpoints handling unchanged except for the path move itself.

- [ ] **Step 3: Move example data directory**

Move:

```text
example_data/
-> sandbox/example_data/
```

This keeps sample payloads out of the active CLI surface while preserving them for reference.

- [ ] **Step 4: Move old package/readme-style doc into sandbox**

Move:

```text
docs/waterdata-package-cli-gui.md
-> sandbox/docs/waterdata-package-cli-gui.md
```

If any additional older readmes are clearly no longer the active CLI front door, move them into `sandbox/` at the same time with minimal renaming such as:

```text
sandbox/README-legacy.md
```

Only do this for files that are clearly legacy-facing.

- [ ] **Step 5: Run a filesystem sanity check**

Run:

```bash
find sandbox -maxdepth 3 -type f | sort
```

Expected: the moved GUI, plotting, helper, notebook, example-data, and legacy-doc files appear under `sandbox/`.

## Task 4: Refresh Active Packaging Metadata And Root README

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `tests/test_packaging_config.py`
- Modify: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Update package description and readme path**

Edit `pyproject.toml` so:

- `description` no longer says `CLI and GUI app`
- `readme` points to the active root `README.md` or another kept top-level CLI-facing doc

Keep the package name, version, and dependencies unchanged unless a moved file requires a path update.

- [ ] **Step 2: Keep the root README minimal and product-facing**

Update `README.md` so it remains the active CLI-facing landing page and does not point readers into moved legacy package docs as the primary source of truth.

It should still cover:

- what the tool is
- how to build the Windows `.exe`
- how to run `create-new-project`
- how to run `add-data`

- [ ] **Step 3: Update tests for the new metadata/doc paths**

Adjust any packaging or repo-structure tests so they expect:

- active metadata points at the kept README
- legacy doc moved to `sandbox/docs/...`
- GUI references are no longer part of the active package story

- [ ] **Step 4: Run focused packaging tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_packaging_config.py tests/test_waterdata_toolbox_demo_package.py -k "package or build or docs" -v
```

Expected: PASS

## Task 5: Final Structural Verification

**Files:**
- Verify the repo layout after moves
- Verify active CLI files still import and run

- [ ] **Step 1: Run the full active package test files**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_packaging_config.py tests/test_waterdata_toolbox_demo_package.py -v
```

Expected: PASS

- [ ] **Step 2: Run one CLI help smoke test**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo
```

Expected: CLI help output with no GUI import/runtime path required.

- [ ] **Step 3: Run one active workflow smoke test**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --output-dir dist/outputs/cli_shp_smoke
```

Expected:

- command still succeeds
- active CLI workflow still writes `discharge.shp`
- no GUI code is needed from the active package surface

- [ ] **Step 4: Review final repo boundary**

Run:

```bash
find src/waterdata_toolbox_demo -maxdepth 1 -type f | sort
find sandbox -maxdepth 3 -type f | sort
```

Expected:

- active `src/waterdata_toolbox_demo/` contains only CLI-facing product files
- sandbox contains moved GUI/legacy materials
- `tests/` remains top level

- [ ] **Step 5: Stop for user review**

Do not commit. Summarize:

- which files moved to `sandbox/`
- which active product files changed
- whether tests passed
- whether the CLI smoke tests still passed
- any follow-up cleanup still worth doing later, especially README rewrites or deeper legacy doc pruning
