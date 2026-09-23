# CLI Signature Simplification Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the active CLI so `create-new-project` uses repeatable `--wf` options and `add-data` uses a single positional workflow argument, while keeping workflow behavior unchanged.

**Architecture:** Keep the internal workflow mapping exactly as it is today, but replace the three-boolean workflow selection pattern in `cli.py` with a repeatable `--wf` option for `create-new-project` and a required positional workflow for `add-data`. Update tests and user-facing docs together so the parser, help output, and examples all reflect the same contract.

**Tech Stack:** Python, argparse, pytest

---

## File Map

- Modify: `src/waterdata_toolbox_demo/cli.py`
  - replace `--discharge/--daily/--periodic`
  - add repeatable `--wf` for `create-new-project`
  - add positional workflow for `add-data`
  - add clearer `help=` text
- Modify: `tests/test_cli_repo_boundary.py`
  - add or update parser-level and help-surface tests for the new CLI signature
- Modify: `README.md`
  - update active CLI usage examples
- Modify: `sandbox/docs/waterdata-package-cli-gui.md`
  - update the legacy package note if it still shows the old signature

## Implementation Notes

- Do not change the internal workflow ids:
  - `discharge` -> `discharge`
  - `daily` -> `gw_daily`
  - `periodic` -> `gw_periodic`
- Do not change output formats or retrieval logic.
- Do not commit during execution unless the user explicitly asks.

## Task 1: Lock The New CLI Signature With Failing Tests

**Files:**
- Modify: `tests/test_cli_repo_boundary.py`
- Reference: `src/waterdata_toolbox_demo/cli.py`

- [ ] **Step 1: Add a failing parser test for repeatable `--wf` on `create-new-project`**

Add a parser-level test that expects:

```python
args = build_parser().parse_args(
    ["create-new-project", "--wf", "discharge", "--wf", "daily"]
)
```

and then asserts the parsed `wf` values are:

```python
["discharge", "daily"]
```

Expected initial result: FAIL because the parser still uses boolean workflow flags.

- [ ] **Step 2: Add a failing parser test for positional workflow on `add-data`**

Add a test that expects:

```python
args = build_parser().parse_args(
    ["add-data", "discharge", "--station-id", "02225500", "--parameter-code", "00060"]
)
```

and asserts:

```python
args.workflow == "discharge"
```

Expected initial result: FAIL because `add-data` currently expects workflow booleans.

- [ ] **Step 3: Add a failing CLI help-surface test**

Add a test that checks the parser help text or command help text includes:

- `--wf`

and no longer includes:

- `--discharge`
- `--daily`
- `--periodic`

for active CLI workflow selection.

- [ ] **Step 4: Run the focused CLI parser tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_repo_boundary.py -v
```

Expected: FAIL on the new parser/signature assertions.

## Task 2: Replace Boolean Workflow Flags In `cli.py`

**Files:**
- Modify: `src/waterdata_toolbox_demo/cli.py`
- Test: `tests/test_cli_repo_boundary.py`

- [ ] **Step 1: Replace `_add_workflow_flags(...)` with a repeatable `--wf` helper**

In `cli.py`, remove the shared boolean-flag helper and add a new helper for:

```python
parser.add_argument(
    "--wf",
    action="append",
    choices=["discharge", "daily", "periodic"],
    help="Workflow to run. Repeat to include more than one workflow.",
)
```

Use it only for `create-new-project`.

- [ ] **Step 2: Add positional workflow parsing for `add-data`**

For `add-data`, replace the current workflow flags with one required positional:

```python
add_parser.add_argument(
    "workflow",
    choices=["discharge", "daily", "periodic"],
    help="Workflow to run.",
)
```

- [ ] **Step 3: Add explicit help text for the rest of the active arguments**

Add `help=` text for:

- `--bbox`
- `--output-dir`
- `--station-id`
- `--parameter-code`
- `--start-date`
- `--end-date`

Also make the bbox help mention the order:

```text
WEST SOUTH EAST NORTH
```

- [ ] **Step 4: Replace `_selected_workflows(args)` with new workflow selectors**

Update the dispatch logic so:

- `create-new-project` uses `args.wf`
- `add-data` uses `args.workflow`

Then map those human-facing values to the current internal workflow ids through the existing `_WORKFLOW_FLAG_MAP` concept, likely renamed to better fit the new signature.

- [ ] **Step 5: Remove obsolete validation for “exactly one of three flags”**

Delete the old parser/runtime checks that enforce:

- at least one of `--discharge/--daily/--periodic`
- exactly one of `--discharge/--daily/--periodic`

Replace them with checks appropriate to:

- repeatable `--wf` for `create-new-project`
- required positional `workflow` for `add-data`

- [ ] **Step 6: Run the focused CLI parser tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_repo_boundary.py -v
```

Expected: PASS

## Task 3: Update The Active CLI Docs

**Files:**
- Modify: `README.md`
- Modify: `sandbox/docs/waterdata-package-cli-gui.md`

- [ ] **Step 1: Update root README examples**

Replace old boolean workflow examples with:

```text
create-new-project --wf discharge --wf daily
add-data discharge --station-id 02225500 --parameter-code 00060
```

Keep the rest of the active root README content intact unless it directly refers to the old signature.

- [ ] **Step 2: Update the sandboxed legacy package note**

Update `sandbox/docs/waterdata-package-cli-gui.md` so its CLI examples also reflect:

- `--wf` for `create-new-project`
- positional workflow for `add-data`

This keeps the reference material consistent even though it lives under `sandbox/`.

- [ ] **Step 3: Run a quick help smoke test**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --help
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo add-data --help
```

Expected:

- `create-new-project` help shows `--wf`
- `add-data` help shows positional workflow
- old boolean workflow flags are gone

## Task 4: Full Verification

**Files:**
- Verify active CLI parsing and workflow dispatch

- [ ] **Step 1: Run top-level tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests -v
```

Expected: PASS

- [ ] **Step 2: Run one `create-new-project` smoke test with the new signature**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --wf discharge --output-dir dist/outputs/cli_shp_smoke
```

Expected:

- command succeeds
- `dist/outputs/cli_shp_smoke/discharge.shp` is written

- [ ] **Step 3: Run one `add-data` smoke test with the new signature**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo add-data discharge --station-id 02225500 --parameter-code 00060 --output-dir dist/outputs/cli_csv_smoke
```

Expected:

- command succeeds
- `dist/outputs/cli_csv_smoke/discharge_02225500.csv` is written

- [ ] **Step 4: Stop for user review**

Do not commit. Summarize:

- parser/help changes
- doc updates
- whether tests passed
- whether the new-signature smoke tests passed
