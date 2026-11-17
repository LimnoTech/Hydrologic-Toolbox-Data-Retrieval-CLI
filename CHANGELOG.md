# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

The previous release is v0.1.0 (tag `v0.1.0`, 2026-09-23).

### Breaking (Toolbox contract)

None so far.

### Added

- A top-level `--version` flag. The version now comes from git tags through hatch-vcs.
- pixi environments `default`, `ci` and `build`, with a committed `pixi.lock`, for linux-64,
  osx-arm64 and win-64. pixi 0.84.2 or newer is required, and CI pins that version.
- pixi tasks `test`, `test-live`, `lint`, `format`, `typecheck`, `cli` and `build-exe`.
- A GitHub Actions workflow. On a push, Ubuntu runs the offline tests, lint, the format check
  and the type check. On pull requests into `main` and on manual runs, Ubuntu, macOS and Windows
  run the tests, lint and format check, with the type check on Ubuntu. A Windows executable build
  runs on pull requests into `main`, on manual runs and on `v*` tags: it smoke-tests the exe,
  measures the bundle, uploads the bundle folder as an artifact, and on a `v*` tag attaches the
  zip to a draft release. Changes touching only markdown or `.gitignore` do not trigger branch or
  pull request runs.
- A `build-exe` step that refreshes the generated version before PyInstaller runs, so a local
  build never embeds a stale version.
- One dependency list. The runtime dependencies are `[project.dependencies]` alone, and the
  repo is a pixi-build source package: pixi maps that list to conda names, and every pixi
  environment installs the package through it. `geopandas` maps to conda's `geopandas-base`, so
  scipy, scikit-learn, mapclassify, matplotlib, pyogrio and GDAL are no longer installed; the CLI
  uses none of them. A test checks that every dependency reaches the locked package record. A
  checkout made before this change needs
  `pixi reinstall -e <env> hydrologic-toolbox-data-retrieval-cli` once per environment, because
  the editable self-install became a source package.
- No `pyarrow`, by measurement, and a test keeps it out of the lock. On the Windows runner it
  added 23.9 MB to the zipped exe bundle (296.5 to 320.4 MB) and 0.04 s to `--help`. On macOS
  with pandas 3.1.1 it gave nothing the Toolbox would notice: the CLI's dataretrieval calls all
  take the OGC JSON path, where building the tables was 7-10% slower with it; `to_csv` was
  unchanged; memory fell 60-65%, on tables of a few MB; and pandas 3 does not switch `read_csv`
  to the pyarrow engine.
- On win-64, OpenBLAS as the BLAS, so Intel MKL's DLLs stay out of the exe. With that and
  the leaner geopandas, the zipped Windows exe bundle is 59.4 MB, against 243 MB for v0.1.0.
- A 250 MB limit on the zipped Windows exe bundle: `scripts/measure_bundle.py --max-mb` fails
  the CI build above it, after writing the size row to the job summary.
- A pixi `jupyter` feature (JupyterLab, jupytext, matplotlib, ipykernel), carried by the
  `default` environment.
- Licence and project metadata in `pyproject.toml`: the MIT licence file, authors, maintainers,
  keywords, classifiers and project URLs.
- A `Development` section, a "Run without the exe" section and a `Credits` section in the
  README.

### Changed

- Packaging moved to hatchling and hatch-vcs.
- Offline tests are the default for `pytest`; tests marked `live` are deselected unless run with
  `test-live`.
- The code base is formatted with ruff and passes the ruff lint baseline.
- `dataretrieval` is constrained to `>=1.3,<1.4`.
- The README's build instructions use pixi.

### Removed

- The `pip install -e ".[build]"` extra; build with `pixi run -e build build-exe`.
- Spec tests that imported the pre-rename package.
