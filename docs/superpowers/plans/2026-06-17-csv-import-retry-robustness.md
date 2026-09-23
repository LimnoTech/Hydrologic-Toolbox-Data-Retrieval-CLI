# CSV Import And Retry Robustness Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make add-data CSV output import reliably into Hydrologic Toolbox by force-quoting text-like metadata fields and writing CSV outputs with retry-safe replacement.

**Architecture:** Keep the existing add-data schema intact. Centralize forced-quote field policies in `exports.py`, continue using the existing CSV formatting helpers, and add an atomic-write wrapper around time-series CSV export so retries replace final outputs only after a complete write succeeds.

**Tech Stack:** Python, pandas, csv, pathlib, pytest

---

## File Map

**Create:**
- `tests/test_csv_export_assumptions.py`
  - Characterization tests proving `CategoricalDtype` does not control CSV quoting and the exporter forced-quote policy does.

**Modify:**
- `src/waterdata_toolbox_demo/exports.py`
  - Add named forced-quote field sets.
  - Apply those sets to reduced discharge/daily headers and periodic headers.
  - Write time-series CSVs through a temporary sibling file and atomically replace the final file.
- `tests/test_cli_signature.py`
  - Tighten existing CSV assertions for discharge/daily and periodic metadata quoting.
- `docs/superpowers/specs/2026-06-17-csv-import-retry-robustness-design.md`
  - Keep rationale for why `CategoricalDtype` is not the fix.

**Reference:**
- `src/waterdata_toolbox_demo/timeseries.py`
  - Builds the metadata values that `exports.py` serializes.

## Task 1: Capture the CategoricalDtype CSV Assumption

**Files:**
- Create: `tests/test_csv_export_assumptions.py`
- Reference: `src/waterdata_toolbox_demo/exports.py`

- [ ] **Step 1: Add a characterization test for pandas categorical CSV output**

Add:

```python
def test_categorical_dtype_does_not_force_csv_quotes():
    category_dtype = pd.CategoricalDtype()
    frame = pd.DataFrame(
        {
            "site_no": pd.Series(["04193500"], dtype=category_dtype),
            "Station name": pd.Series(["MAUMEE RIVER AT WATERVILLE OH"], dtype=category_dtype),
            "HUC code": pd.Series(["04100009"], dtype=category_dtype),
        }
    )

    lines = frame.to_csv(index=False).splitlines()

    assert lines[1] == "04193500,MAUMEE RIVER AT WATERVILLE OH,04100009"
    assert '"' not in lines[1]
```

- [ ] **Step 2: Add a characterization test for exporter forced quotes**

Add:

```python
def test_forced_quote_fields_are_the_csv_quoting_control():
    from waterdata_toolbox_demo.exports import _format_csv_line

    fields = ["site_no", "Station name", "HUC code"]
    values = ["04193500", "MAUMEE RIVER AT WATERVILLE OH", "04100009"]

    line = _format_csv_line(
        values,
        forced_quote_fields=set(fields),
        field_names=fields,
    )

    assert line == '"04193500","MAUMEE RIVER AT WATERVILLE OH","04100009"'
```

- [ ] **Step 3: Run the characterization tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_csv_export_assumptions.py -v
```

Expected:
- `2 passed`

## Task 2: Force Quote Reduced Discharge/Daily Metadata Text Fields

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_cli_signature.py`

- [ ] **Step 1: Add a focused reduced-header unit test**

Add or update a test that writes a reduced `discharge` CSV with metadata:

```python
csv_header_metadata = {
    "site_no": "USGS-04193500",
    "Description": "Discharge, cubic feet per second",
    "Parameter": "00060",
    "Statistic": "00003",
    "TS_ID": "123",
    "IV_TS_ID": "",
    "Site number": "04193500",
    "Station name": "MAUMEE RIVER AT WATERVILLE OH",
    "Latitude": 41.5,
    "Longitude": -83.7,
    "HUC code": "04100009",
    "Drainage area": 6330.0,
}
```

Assert the metadata value line contains:

```text
# "USGS-04193500","Discharge, cubic feet per second","00060","00003",123,,"04193500","MAUMEE RIVER AT WATERVILLE OH",41.5,-83.7,"04100009",6330.0
```

The exact numeric formatting can follow the current `_csv_safe_value(...)` output.

- [ ] **Step 2: Verify the test fails before the implementation**

Run the focused test.

Expected:
- fail because `site_no`, `Site number`, `Station name`, and `HUC code` are not all force-quoted yet.

- [ ] **Step 3: Add the reduced-header quote policy**

In `exports.py`, add:

```python
_REDUCED_CSV_FORCED_QUOTE_FIELDS = {
    "site_no",
    "Description",
    "Parameter",
    "Statistic",
    "Site number",
    "Station name",
    "HUC code",
}
```

- [ ] **Step 4: Use the quote policy in the reduced-header writer**

Replace:

```python
forced_quote_fields={"Parameter", "Statistic"},
```

with:

```python
forced_quote_fields=_REDUCED_CSV_FORCED_QUOTE_FIELDS,
```

- [ ] **Step 5: Run the focused reduced-header test**

Expected:
- pass

## Task 3: Force Quote Periodic Metadata Identifier Fields

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_cli_signature.py` or create a focused test in `tests/test_csv_export_assumptions.py`

- [ ] **Step 1: Add a focused periodic-header test**

Write a periodic CSV with metadata that includes:

```python
csv_header_metadata = {
    "monitoring_location_id": "USGS-410947071344803",
    "monitoring_location_number": "410947071344803",
    "monitoring_location_name": "RI-NHW  258 NEW SHOREHAM (BLOCK ISLAND)",
    "site_type_code": "GW",
    "hydrologic_unit_code": "01100007",
    "vertical_datum": "NAVD88",
}
```

Assert the periodic metadata value line force-quotes each text/code value.

- [ ] **Step 2: Verify the test fails before the implementation**

Run the focused test.

Expected:
- fail because only `monitoring_location_name` is force-quoted today.

- [ ] **Step 3: Add the periodic-header quote policy**

In `exports.py`, add:

```python
_PERIODIC_CSV_FORCED_QUOTE_FIELDS = {
    "monitoring_location_id",
    "monitoring_location_number",
    "monitoring_location_name",
    "site_type_code",
    "hydrologic_unit_code",
    "vertical_datum",
    "district_code",
    "state_code",
    "county_code",
    "country_code",
    "time_zone_abbreviation",
    "national_aquifer_code",
    "aquifer_code",
    "aquifer_type_code",
    "depth_source_code",
}
```

- [ ] **Step 4: Use the quote policy in the periodic-header writer**

Replace:

```python
forced_quote_fields={"monitoring_location_name"},
```

with:

```python
forced_quote_fields=_PERIODIC_CSV_FORCED_QUOTE_FIELDS,
```

- [ ] **Step 5: Run the focused periodic-header test**

Expected:
- pass

## Task 4: Add Retry-Safe CSV Replacement

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Modify: `tests/test_csv_export_assumptions.py`

- [ ] **Step 1: Add a test that successful writes replace existing CSV content**

Use `export_timeseries_artifacts(...)` or `_write_timeseries_csv_artifact(...)` to write a CSV to a temporary directory that already has an old file at the final path.

Assert:

- the final path exists
- old content is gone
- new content is present

- [ ] **Step 2: Add a test that failed writes clean up temporary files**

Monkeypatch the internal writer function or use a frame/value that triggers a controlled exception during writing.

Assert:

- the final existing CSV remains unchanged
- no sibling temporary CSV file remains

- [ ] **Step 3: Verify the tests fail before the implementation**

Expected:
- the replacement test may already pass by direct overwrite
- the failure cleanup test should fail because there is no atomic temp path yet

- [ ] **Step 4: Add a private atomic CSV helper**

In `exports.py`, add a helper shaped like:

```python
def _write_csv_atomically(csv_path, write_callback):
    temporary_path = csv_path.with_name(f".{csv_path.name}.tmp")
    try:
        write_callback(temporary_path)
        temporary_path.replace(csv_path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
```

- [ ] **Step 5: Move existing CSV write logic behind callbacks**

Refactor `_write_timeseries_csv_artifact(...)` so the selected writer writes to the temporary path and then replaces the final CSV.

Keep the public return value unchanged.

- [ ] **Step 6: Run the retry-safe CSV tests**

Expected:
- pass

## Task 5: Run Regression Verification

**Files:**
- Reference: `tests/test_csv_export_assumptions.py`
- Reference: `tests/test_cli_signature.py`
- Reference: `tests/test_xml_compat.py`

- [ ] **Step 1: Run focused CSV tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_csv_export_assumptions.py -v
```

Expected:
- pass

- [ ] **Step 2: Run non-live CLI signature tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_cli_signature.py -k 'not live' -q
```

Expected:
- pass

- [ ] **Step 3: Run XML compatibility tests**

Run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_xml_compat.py -v
```

Expected:
- pass

## Task 6: Manual Smoke Test After Rebuild

**Files:**
- Reference: `README.md`
- Reference: `waterdata_toolbox_demo.spec`

- [ ] **Step 1: Rebuild the Windows executable**

On Windows, run:

```powershell
python -m pip install -e .[build]
pyinstaller waterdata_toolbox_demo.spec
```

- [ ] **Step 2: Run the known client discharge station**

Run:

```cmd
waterdata_toolbox_demo.exe add-data discharge --station-id 04193500 --output-dir C:\temp\wdt_test
```

Expected:
- `C:\temp\wdt_test\discharge_04193500.csv` is written
- metadata line quotes `Station name`, `Site number`, `site_no`, and `HUC code`

- [ ] **Step 3: Retry the same command**

Run the same command again.

Expected:
- the output file is replaced cleanly
- Hydrologic Toolbox can import the CSV and plot the data
