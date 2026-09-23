# PyInstaller Startup Speed Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the default Windows package launch much faster by switching the PyInstaller build from one-file extraction to an onedir distribution.

**Architecture:** Keep the Python app entrypoint unchanged and change only the packaging layer. Update the PyInstaller spec so the default artifact is an application directory with an `.exe` inside it, then align the build instructions so they point to the new output path and explain the startup-speed tradeoff.

**Tech Stack:** Python, PyInstaller, pytest, markdown docs

---

## File Map

- Modify: `waterdata_toolbox_demo.spec`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Create: `tests/test_packaging_config.py`

### Task 1: Lock in the new packaging contract with a failing test

**Files:**
- Create: `tests/test_packaging_config.py`

- [ ] **Step 1: Write the failing packaging test**

Add a focused test that asserts the default PyInstaller spec uses `COLLECT(...)` and `exclude_binaries=True`, which together indicate an onedir build rather than a one-file executable.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `python -m pytest tests/test_packaging_config.py -v`
Expected: FAIL because the current spec still builds a one-file executable.

### Task 2: Switch the default build to onedir and update instructions

**Files:**
- Modify: `waterdata_toolbox_demo.spec`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Test: `tests/test_packaging_config.py`

- [ ] **Step 1: Update the PyInstaller spec**

Change the spec to:
- build an `EXE(...)` with `exclude_binaries=True`
- add `COLLECT(...)` so PyInstaller emits `dist/waterdata_toolbox_demo/`
- disable UPX compression to avoid extra startup cost on the unpacked app

- [ ] **Step 2: Update packaging docs**

Document that:
- the default Windows build is now an onedir app for faster startup
- the runnable executable lives at `dist/waterdata_toolbox_demo/waterdata_toolbox_demo.exe`
- the tradeoff is a folder-based distribution instead of a single standalone file

- [ ] **Step 3: Re-run the focused test**

Run: `python -m pytest tests/test_packaging_config.py -v`
Expected: PASS
