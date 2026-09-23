# Notebook Helper Support Refactor Design

## Goal

Refactor the USGS waterdata demo notebook so the real `dataretrieval.waterdata` retrieval functions remain visible in the notebook, while support utilities such as station normalization and widget rendering move into `helpers/usgs_waterdata_demo.py`.

The notebook should also add docstrings to every function that remains defined in notebook cells.

## Context

The current notebook already:

- keeps `wd.get_monitoring_locations`, `wd.get_time_series_metadata`, `wd.get_field_measurements`, and `wd.get_daily` usage in notebook-local retrieval functions
- includes section-specific plotting for `Creating New Project` and `Adding Data to Project`
- uses helper imports for config and export support

The new request changes the notebook/helper boundary:

- hide support plumbing in `helpers/`
- keep the live `waterdata` API calls in the notebook because this is still a demo
- do not reintroduce repo-root bootstrap checks
- add docstrings to every notebook-defined function

## Requirements

- Keep the actual `waterdata` retrieval/demo functions in the notebook:
  - `get_usgs_stations_in_bbox(...)`
  - `run_create_new_project_section(...)`
  - `get_usgs_timeseries(...)`
  - `run_add_data_to_project_section(...)`
- Move support helpers into `helpers/usgs_waterdata_demo.py`
- Move all widget rendering helpers into `helpers/usgs_waterdata_demo.py`
- Do not move direct `waterdata` service calls into `helpers/`
- Do not re-add the repo-root detection/bootstrap checks the user removed
- Add docstrings to every function still defined in the notebook
- Keep the notebook behavior and rendered outputs functionally the same

## Recommended Approach

Use a split where the notebook owns workflow intent and live API usage, while `helpers/` owns formatting, normalization, and widget plumbing.

This preserves the teaching value of the notebook because readers still see the real `waterdata` calls and arguments in context. At the same time, it shortens the notebook by moving reusable support code out of the visible demo flow.

## Notebook Responsibilities

Keep these responsibilities in `notebooks/usgs_waterdata_demo.ipynb`:

- explanatory markdown and legacy-link notes
- notebook-local `waterdata` retrieval functions
- section orchestration for `Creating New Project` and `Adding Data to Project`
- top-level render cells that call imported support helpers

Every notebook-defined function should include a short docstring that explains its purpose.

## Helper Responsibilities

Expand `helpers/usgs_waterdata_demo.py` to include notebook support helpers such as:

- geometry-to-coordinate extraction support
- station-frame normalization and legacy column shaping
- station plot-frame preparation
- station plot rendering
- station widget rendering
- add-data plot-frame preparation
- add-data plot rendering
- add-data widget rendering
- existing export and artifact-message utilities

These helpers should be generic around DataFrames and plotting inputs. They should not call `waterdata` directly.

## Notebook Imports

The notebook should import the new support helpers from `helpers/usgs_waterdata_demo.py` alongside existing imports such as:

- `DEMO_CONFIG`
- `NOTEBOOK_MAPPING_ROWS`
- `export_timeseries_artifacts`
- `format_artifact_messages`

The notebook should no longer define the moved support helpers locally.

## Testing

Update tests so they verify:

- the notebook still defines the retrieval/demo functions locally
- the notebook imports the moved support helpers from `helpers/usgs_waterdata_demo.py`
- the notebook no longer defines the moved widget/rendering helpers locally
- every notebook-defined function has a docstring
- helper behavior still covers:
  - station normalization output shape
  - plot-frame preparation
  - plot rendering behavior
  - export behavior

## Verification

After implementation:

- rerun `tests/test_usgs_waterdata_demo.py`
- execute `notebooks/usgs_waterdata_demo.ipynb`
- confirm the notebook still:
  - shows both workflow sections
  - renders both widgets
  - keeps add-data artifact writing intact
  - keeps create-project display-only behavior intact

## Out of Scope

- changing the legacy workflow structure
- moving the live `waterdata` retrieval calls into helpers
- reintroducing repo-root checks
- changing output artifact formats
- changing the user-facing workflow split between the two sections
