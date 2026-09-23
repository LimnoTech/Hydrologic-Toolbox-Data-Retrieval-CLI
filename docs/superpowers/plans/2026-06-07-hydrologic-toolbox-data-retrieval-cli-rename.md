# Hydrologic-Toolbox-Data-Retrieval-CLI Rename Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the active CLI package, module path, spec, tests, and README references to `Hydrologic-Toolbox-Data-Retrieval-CLI` with no backward compatibility layer.

**Architecture:** Treat this as a clean package-surface rename rather than a behavior change. Update tests first so the new module path and CLI branding are the expected contract, then rename the source package and metadata, and finally rewrite README/spec references and verify the active package surface is free of the old name.

**Tech Stack:** Python, setuptools, PyInstaller, pytest, ripgrep

---

### Task 1: Lock the New Public Contract in Tests

**Files:**
- Modify: `tests/test_cli_signature.py`
- Modify: `tests/test_xml_compat.py`

- [ ] **Step 1: Write the failing test expectations**

Update the tests to import `hydrologic_toolbox_data_retrieval_cli`, run `python -m hydrologic_toolbox_data_retrieval_cli`, and assert help text includes `hydrologic-toolbox-data-retrieval-cli`.

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python -m pytest tests/test_cli_signature.py tests/test_xml_compat.py -q`
Expected: FAIL because the renamed module path does not exist yet and old help text still uses the old CLI name.

- [ ] **Step 3: Commit test-first progress if desired**

Optional once the red state is confirmed.

### Task 2: Rename the Package Surface

**Files:**
- Move: `src/waterdata_toolbox_demo/` -> `src/hydrologic_toolbox_data_retrieval_cli/`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/__init__.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/__main__.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/app.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/cli.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/config.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/exports.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/station_discovery.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/timeseries.py`
- Modify: `src/hydrologic_toolbox_data_retrieval_cli/xml_compat.py`

- [ ] **Step 1: Rename the package directory and internal imports**

Update all `waterdata_toolbox_demo.*` imports to `hydrologic_toolbox_data_retrieval_cli.*` and rewrite user-facing docstrings/help text to the new name.

- [ ] **Step 2: Keep behavior unchanged**

Do not alter CLI arguments, XML routing, export semantics, or workflow defaults beyond branding and module-path references.

- [ ] **Step 3: Run the targeted tests to verify they pass**

Run: `python -m pytest tests/test_cli_signature.py tests/test_xml_compat.py -q`
Expected: PASS

### Task 3: Rename Packaging Metadata and Build Surface

**Files:**
- Modify: `pyproject.toml`
- Move: `waterdata_toolbox_demo.spec` -> `hydrologic_toolbox_data_retrieval_cli.spec`
- Modify: `src/waterdata_toolbox_demo.egg-info/PKG-INFO`
- Modify: `src/waterdata_toolbox_demo.egg-info/entry_points.txt`
- Modify: `src/waterdata_toolbox_demo.egg-info/top_level.txt`
- Modify: `src/waterdata_toolbox_demo.egg-info/SOURCES.txt`

- [ ] **Step 1: Rename the package metadata**

Set the project name and console script to the new identifiers, and update the spec to point at the renamed module path and output name.

- [ ] **Step 2: Refresh tracked metadata files**

Update any tracked egg-info files that are part of the repo so the active tree does not advertise the old package name.

- [ ] **Step 3: Run a focused packaging smoke check**

Run: `python -m hydrologic_toolbox_data_retrieval_cli --help`
Expected: exit 0 and help output headed by `hydrologic-toolbox-data-retrieval-cli`

### Task 4: Rewrite README and Verify Website References

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite the README branding**

Replace the old executable/package name with the new tool name in the title, examples, and command table.

- [ ] **Step 2: Add the website section**

Add links for the Hydrologic Toolbox site, the USGS Water Data APIs overview, and the USGS Water Data API hub.

- [ ] **Step 3: Keep XML compatibility documentation intact**

Preserve the existing XML examples and behavior notes, only updating names and paths where required.

### Task 5: Final Verification

**Files:**
- Verify: `README.md`
- Verify: `pyproject.toml`
- Verify: `hydrologic_toolbox_data_retrieval_cli.spec`
- Verify: `src/hydrologic_toolbox_data_retrieval_cli/`
- Verify: `tests/test_cli_signature.py`
- Verify: `tests/test_xml_compat.py`

- [ ] **Step 1: Run the active test suite**

Run: `python -m pytest tests/test_cli_signature.py tests/test_xml_compat.py -q`
Expected: PASS

- [ ] **Step 2: Search for stale active-package references**

Run: `rg -n "waterdata-toolbox-demo|waterdata_toolbox_demo|Water Data ToolBox" README.md pyproject.toml src tests hydrologic_toolbox_data_retrieval_cli.spec`
Expected: no stale hits in the active package surface, except intentional historical references if any remain outside the active surface.

- [ ] **Step 3: Report residual stale references outside active surface**

Call out any remaining mentions in historical planning/spec docs if they are intentionally left untouched.
