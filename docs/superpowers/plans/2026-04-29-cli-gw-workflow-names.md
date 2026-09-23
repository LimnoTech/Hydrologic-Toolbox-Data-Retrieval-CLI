# CLI GW Workflow Names Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the user-facing groundwater workflow names in the CLI from `daily` and `periodic` to `gw_daily` and `gw_periodic`.

**Architecture:** Simplify the parser to accept the internal workflow ids directly instead of aliasing user-facing short names. Then align docs and local CLI tests with the new command surface.

**Tech Stack:** Python, argparse, pytest, Markdown

---

### Task 1: Update the parser surface

**Files:**
- Modify: `src/waterdata_toolbox_demo/cli.py`

- [ ] Replace the alias map so the accepted workflow names are `discharge`, `gw_daily`, and `gw_periodic`.
- [ ] Remove the extra user-facing alias translation where it is no longer needed.
- [ ] Verify `create-new-project --help` and `add-data --help` show the new names.

### Task 2: Update product-facing docs

**Files:**
- Modify: `README.md`
- Modify: `sandbox/docs/waterdata-package-cli-gui.md`

- [ ] Replace `daily` examples with `gw_daily`
- [ ] Replace `periodic` examples with `gw_periodic`
- [ ] Update any short explanatory bullets that list accepted workflow names

### Task 3: Update focused local CLI tests

**Files:**
- Modify: `tests/test_cli_required_bbox.py`
- Create or modify as needed: `tests/test_cli_workflow_names.py`

- [ ] Add parser coverage that accepts `gw_daily` and `gw_periodic`
- [ ] Add parser coverage that rejects the old `daily` and `periodic` names
- [ ] Keep the existing required-`--bbox` coverage intact

### Task 4: Verify locally

**Files:**
- Verify source, docs, and tests

- [ ] Run the focused CLI tests
- [ ] Run `create-new-project --help`
- [ ] Run `add-data --help`
- [ ] Confirm the docs match the actual parser choices
