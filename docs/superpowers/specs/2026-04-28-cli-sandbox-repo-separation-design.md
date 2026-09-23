# CLI Sandbox Repo Separation Design

## Summary

The repo should be reshaped so the top-level product surface reflects only the active CLI application and its Windows `.exe` build path. Non-CLI code and legacy project material should move under a top-level `sandbox/` directory, with one explicit exception: `tests/` stays at the repo root.

## Goals

- Make the repo read as a CLI-first product at the top level.
- Move GUI code and other non-CLI material out of the active product surface.
- Move old readmes and legacy/docs material into `sandbox/`.
- Keep generated or ignored files untouched and still ignored.
- Keep `tests/` at the repo root.

## Non-Goals

- Rewriting all readmes during this move.
- Deleting legacy material.
- Redesigning the CLI behavior itself.
- Changing the Water Data workflow logic beyond import/path cleanup needed for the move.

## Product Boundary

### Active CLI product files that stay in place

These should remain in the active top-level product structure:

- `src/waterdata_toolbox_demo/__init__.py`
- `src/waterdata_toolbox_demo/__main__.py`
- `src/waterdata_toolbox_demo/app.py`
- `src/waterdata_toolbox_demo/cli.py`
- `src/waterdata_toolbox_demo/config.py`
- `src/waterdata_toolbox_demo/exports.py`
- `src/waterdata_toolbox_demo/station_discovery.py`
- `src/waterdata_toolbox_demo/timeseries.py`
- `pyproject.toml`
- `requirements.txt`
- `waterdata_toolbox_demo.spec`
- `README.md`
- `tests/`

### Non-CLI material that moves to `sandbox/`

These should move under `sandbox/`:

- `src/waterdata_toolbox_demo/gui.py`
- `src/waterdata_toolbox_demo/plotting.py`
- `helpers/`
- `notebooks/`
- `example_data/`
- old or non-product markdown/docs such as:
  - `docs/waterdata-package-cli-gui.md`
  - legacy readmes or package notes that are no longer the active repo front door

### Explicit exception

`tests/` stays top level even though some tests may cover legacy or sidecar behavior. That exception is intentional and should be preserved during this cleanup.

## Sandbox Structure

The `sandbox/` directory should act as a holding area for non-CLI repo material, not a new package. A simple structure is enough:

- `sandbox/src/waterdata_toolbox_demo/gui.py`
- `sandbox/src/waterdata_toolbox_demo/plotting.py`
- `sandbox/helpers/...`
- `sandbox/notebooks/...`
- `sandbox/example_data/...`
- `sandbox/docs/...`
- `sandbox/README-legacy.md` or equivalent moved legacy readmes

The exact subpaths may mirror the current repo layout when that makes the move easier to understand.

## Entry Point Cleanup

The active CLI app should stop advertising or importing the GUI path from the main product surface.

### `app.py`

- Remove the `run_gui()` helper.
- Keep `main()` CLI-only.
- Preserve the current behavior where no arguments routes to CLI help.

### `pyproject.toml`

- Update package metadata so it no longer describes the project as a CLI-and-GUI app.
- Point the package `readme` to the active root `README.md` or another active CLI-facing file that stays outside `sandbox/`.

### `waterdata_toolbox_demo.spec`

- Remove GUI-specific hidden imports or packaging references if they only exist for the sandboxed GUI.

## README and Docs Strategy

### Root README

Keep a minimal active root `README.md` that focuses on:

- what the CLI product is
- how to build the Windows `.exe`
- how to run `create-new-project`
- how to run `add-data`

### Legacy readmes/docs

Move older readmes and notes into `sandbox/` for now instead of trying to rewrite them during the same change.

### Superpowers docs

The `docs/superpowers/...` planning/spec files can stay where they are unless you later decide to archive them separately. They are process artifacts, not part of the runtime product surface.

## Tests

`tests/` remains at repo root.

This move should not attempt a major test reorganization unless a path change is strictly required by moved files. If any tests reference files that move to `sandbox/`, update those references minimally so the test suite still works.

## Ignored and Generated Files

Anything already ignored should stay ignored and should not be part of the structural cleanup plan. That includes generated outputs, local build artifacts, caches, and other gitignored content.

## Implementation Impact

### Likely code changes

- import cleanup in `app.py`
- packaging metadata cleanup in `pyproject.toml`
- PyInstaller cleanup in `waterdata_toolbox_demo.spec`
- possibly doc/test path updates if tests or metadata currently point at moved docs

### Likely file moves

- move GUI and plotting modules under `sandbox/`
- move helper/notebook/demo data under `sandbox/`
- move old package/readme docs under `sandbox/`

## Acceptance Criteria

- The top-level repo reads as a CLI-first product.
- GUI code no longer lives in the active `src/waterdata_toolbox_demo/` product surface.
- Legacy/non-CLI materials are moved under `sandbox/`.
- Root `README.md` remains active and product-facing.
- `tests/` stays top level.
- Ignored/generated files are left alone.

## Notes

This design is intentionally a structural cleanup, not a product rewrite. The goal is to make the active CLI easier to understand and package, while preserving older material in a clearly separated sandbox area instead of deleting it.
