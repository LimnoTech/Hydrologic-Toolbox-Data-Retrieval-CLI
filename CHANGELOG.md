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
  osx-arm64 and win-64.
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
- A test that keeps the PyPI dependency list and the conda dependency list in step, including
  version floors and ceilings.
- A `jupyter` extra and a matching pixi feature (JupyterLab, jupytext, matplotlib, ipykernel),
  carried by the `default` environment.
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
