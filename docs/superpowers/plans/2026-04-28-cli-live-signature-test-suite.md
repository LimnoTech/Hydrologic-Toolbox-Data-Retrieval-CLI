# CLI Live Signature Test Suite Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fresh CLI-focused test suite that validates the new `--wf` and positional workflow signature, covers key invalid cases offline, and exercises all valid command combinations against the live Water Data endpoints.

**Architecture:** Create one new top-level CLI test module under `tests/` with a small set of shared helpers. Keep invalid and parser-surface checks offline so they are fast and deterministic, then use parametrized live subprocess tests for valid `create-new-project` and `add-data` commands so the real command surface, stdout, and artifacts are verified together.

**Tech Stack:** Python, pytest, subprocess, pathlib

---

## File Map

- Create: `tests/test_cli_signature.py`
  - new CLI-only parser and live command test matrix
- Optional Create: `tests/conftest.py`
  - only if a shared live-command helper or output-root fixture becomes repetitive
- Reference: `src/waterdata_toolbox_demo/cli.py`
  - current command contract and workflow mapping
- Reference: `src/waterdata_toolbox_demo/app.py`
  - packaged app entrypoint behavior
- Reference: `src/waterdata_toolbox_demo/config.py`
  - default bbox, date range, and example station/parameter combinations
- Reference: `src/waterdata_toolbox_demo/station_discovery.py`
  - expected shapefile stems and artifact messages for `create-new-project`
- Reference: `src/waterdata_toolbox_demo/timeseries.py`
  - expected workflow ids and CSV-producing behavior for `add-data`
- Reference: `src/waterdata_toolbox_demo/exports.py`
  - CSV header/body contract and artifact message formatting

## Implementation Notes

- Build the suite around the current signature only:
  - `create-new-project --wf ...`
  - `add-data <workflow> ...`
- Treat invalid cases as parser/CLI surface tests that must not hit the network.
- Treat valid cases as live CLI smoke tests that use subprocesses and real Water Data endpoints.
- Use unique `tmp_path` subdirectories for each live command so artifacts do not collide.
- Run the CLI via:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo ...
```

- Keep assertions high-signal:
  - exit code
  - stdout includes the expected workflow label and row/station count pattern
  - expected output artifacts exist
  - CSV begins with the approved header lines
  - shapefile sidecars exist
- `tests/` is currently gitignored, so this suite will be local-only unless the ignore rules change later.

## Task 1: Scaffold The New CLI Test Module

**Files:**
- Create: `tests/test_cli_signature.py`
- Reference: `src/waterdata_toolbox_demo/cli.py`
- Reference: `src/waterdata_toolbox_demo/config.py`

- [ ] **Step 1: Create the new `tests/` directory and empty test file**

Create:

```text
tests/test_cli_signature.py
```

- [ ] **Step 2: Add import and path bootstrapping**

At minimum, include:

```python
from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
CLI_PYTHON = "/Users/lludden/miniforge3/envs/nhm/bin/python"
```

Also add a helper env builder that prepends `src` to `PYTHONPATH`.

- [ ] **Step 3: Add one shared live-command helper**

Write a helper like:

```python
def run_cli_command(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR)
    return subprocess.run(
        [CLI_PYTHON, "-m", "waterdata_toolbox_demo", *args],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
```

- [ ] **Step 4: Add one shapefile-sidecar assertion helper**

Use a helper like:

```python
def assert_shapefile_set_exists(output_dir: Path, stem: str) -> None:
    for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
        assert (output_dir / f"{stem}{suffix}").exists()
```

- [ ] **Step 5: Add one CSV header assertion helper**

Use a helper like:

```python
def read_first_lines(path: Path, count: int = 3) -> list[str]:
    with path.open(encoding="utf-8") as handle:
        return [handle.readline().rstrip("\n") for _ in range(count)]
```

## Task 2: Lock Invalid CLI Cases Offline

**Files:**
- Modify: `tests/test_cli_signature.py`
- Reference: `src/waterdata_toolbox_demo/cli.py`
- Reference: `src/waterdata_toolbox_demo/app.py`

- [ ] **Step 1: Add a no-args packaged-entrypoint test**

Add a test that confirms:

```python
from waterdata_toolbox_demo import app

result = app.main([])
assert result == 0
```

This keeps the current “empty args -> help” behavior covered in the new suite.

- [ ] **Step 2: Add invalid parser cases for `create-new-project`**

Add parametrized cases for:

- missing `--wf`
- bad `--wf` value
- malformed `--bbox` with too few numbers
- unknown flag

Use `build_parser().parse_args(...)` and assert `SystemExit`.

- [ ] **Step 3: Add invalid parser cases for `add-data`**

Add parametrized cases for:

- missing positional workflow
- bad workflow value
- unexpected extra positional
- unknown flag

Use `build_parser().parse_args(...)` and assert `SystemExit`.

- [ ] **Step 4: Add help-surface assertions**

Add tests that assert:

- `create-new-project --help` includes `--wf {discharge,daily,periodic}`
- `add-data --help` includes `{discharge,daily,periodic}`
- help text does not advertise `--discharge`, `--daily`, or `--periodic` as boolean flags

- [ ] **Step 5: Run just the invalid/parser tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -k "invalid or help or no_args" -v
```

Expected: PASS

## Task 3: Cover All Valid `create-new-project` Workflow Combinations Live

**Files:**
- Modify: `tests/test_cli_signature.py`
- Reference: `src/waterdata_toolbox_demo/config.py`
- Reference: `src/waterdata_toolbox_demo/station_discovery.py`

- [ ] **Step 1: Define the complete non-empty workflow combination matrix**

Use a parametrized list containing:

```python
[
    (["discharge"], ["discharge"]),
    (["daily"], ["daily"]),
    (["periodic"], ["periodic"]),
    (["discharge", "daily"], ["discharge", "daily"]),
    (["discharge", "periodic"], ["discharge", "periodic"]),
    (["daily", "periodic"], ["daily", "periodic"]),
    (["discharge", "daily", "periodic"], ["discharge", "daily", "periodic"]),
]
```

The first list is the CLI `--wf` values. The second list is the expected output stems.

- [ ] **Step 2: Write one live test for the workflow matrix**

For each parameter set:

- build a unique `tmp_path / <case_name>` output directory
- run:

```python
args = ["create-new-project"]
for workflow in workflow_values:
    args.extend(["--wf", workflow])
args.extend(["--output-dir", str(output_dir)])
result = run_cli_command(*args)
```

Assert:

- `result.returncode == 0`
- stdout includes at least one `stations` line
- each expected shapefile set exists using the helper

- [ ] **Step 3: Add one bbox override live test**

Use the approved bbox:

```python
["-82.859", "31.899", "-82.013", "32.947"]
```

Run:

```python
create-new-project --wf periodic --bbox ... --output-dir <tmp>
```

Assert:

- return code `0`
- stdout contains `gw_periodic:` or `periodic.shp`
- `periodic.shp` and sidecars exist

- [ ] **Step 4: Run just the `create-new-project` live tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -k "create_new_project and live" -v
```

Expected: PASS

## Task 4: Cover All Valid `add-data` Workflows Live

**Files:**
- Modify: `tests/test_cli_signature.py`
- Reference: `src/waterdata_toolbox_demo/config.py`
- Reference: `src/waterdata_toolbox_demo/timeseries.py`
- Reference: `src/waterdata_toolbox_demo/exports.py`

- [ ] **Step 1: Define the valid `add-data` live matrix**

Use three explicit cases:

```python
[
    (
        "discharge",
        "02225500",
        "00060",
        None,
        "discharge_02225500.csv",
        "discharge:",
    ),
    (
        "daily",
        "324209082430201",
        "72019",
        None,
        "gw_daily_324209082430201.csv",
        "gw_daily:",
    ),
    (
        "periodic",
        "410947071344803",
        "72019",
        ("1880-01-01", "2100-01-01"),
        "gw_periodic_410947071344803.csv",
        "gw_periodic:",
    ),
]
```

- [ ] **Step 2: Write one parametrized live `add-data` test**

For each case:

- create a unique output directory under `tmp_path`
- build args beginning with:

```python
["add-data", workflow, "--station-id", station_id, "--parameter-code", parameter_code]
```

- for periodic, also append `--start-date` and `--end-date`
- append `--output-dir`
- run via `run_cli_command`

Assert:

- `result.returncode == 0`
- `stdout` contains the expected workflow label
- the expected CSV file exists

- [ ] **Step 3: Add CSV content assertions**

For the resulting CSV:

- read the first three lines
- assert line 1 starts with `# site_no,Description,Parameter,Statistic,TS_ID,IV_TS_ID`
- assert line 2 starts with `# `
- assert line 3 equals `Time,Daily values,Approval status,Qualifier`

Also assert the file has at least one data row after the header block.

- [ ] **Step 4: Run just the `add-data` live tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -k "add_data and live" -v
```

Expected: PASS

## Task 5: Finalize The Full CLI Suite

**Files:**
- Modify: `tests/test_cli_signature.py`

- [ ] **Step 1: Add stable pytest names or comments if needed**

If the module is getting dense, add short section comments such as:

```python
# Offline parser/error coverage
# Live create-new-project coverage
# Live add-data coverage
```

Do not over-abstract unless duplication is clearly painful.

- [ ] **Step 2: Run the full CLI signature suite**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -v
```

Expected: PASS

- [ ] **Step 3: Run one final smoke pass over all tests currently present**

If `tests/` contains only this new suite, run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests -v
```

Expected: PASS

- [ ] **Step 4: Record execution caveats for handoff**

Note explicitly in the final handoff:

- tests hit live USGS endpoints
- failures may reflect network/service instability rather than parser regressions
- `tests/` is gitignored, so the suite is local-only unless ignore rules are changed
