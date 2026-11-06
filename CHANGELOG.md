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
- A GitHub Actions workflow: offline tests on every push and on pull requests into `main` (on
  Ubuntu, macOS and Windows for pull requests), a type check, and a Windows executable build that
  uploads the zipped folder as an artifact and creates a draft release on `v*` tags.
- A `Development` section, a macOS/Linux "Run without the exe" section and a `Credits` section in
  the README.

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
