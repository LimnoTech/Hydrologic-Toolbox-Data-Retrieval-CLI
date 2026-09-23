# NWIS Crosswalk Shapefile Field Names Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current raw-name-plus-suffix shapefile field naming with a code-local NWIS crosswalk that exports only selected fetched monitoring-location values, keeps `dec_lat_va` and `dec_long_va` as geometry-derived DBF fields, and removes the old `_1` / `_2` collision naming behavior.

**Architecture:** Keep the existing `create-new-project` retrieval flow and pure-Python shapefile writer, but change the DBF schema builder in `exports.py` so it is driven by an explicit Water Data -> NWIS alias map instead of arbitrary raw column names. Derive `dec_lat_va` and `dec_long_va` from point geometry during export, validate that the final 10-character NWIS-derived field names are unique, and simplify tests/docs to describe the new compatibility layer rather than the old reduced schema or suffix-based truncation.

**Tech Stack:** Python, pandas, GeoPandas, pyshp, pytest

---

## File Map

- Modify: `src/waterdata_toolbox_demo/exports.py`
  - replace generic raw-column truncation with an explicit crosswalk-driven shapefile schema
  - derive `dec_lat_va` / `dec_long_va` from geometry for DBF export
  - remove the `_1`, `_2` suffix fallback path and fail fast on collisions instead
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
  - keep the filtered monitoring-location frame compatible with the new exporter
  - preserve geometry construction fallback where needed for tests and non-GeoJSON inputs
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
  - replace reduced-schema expectations with NWIS crosswalk expectations
  - add collision-validation coverage for the new fail-fast behavior
  - keep pure-Python shapefile writer coverage intact
- Modify: `docs/create-new-project-shapefile-fields.md`
  - explain the NWIS crosswalk, retained coordinate fields, and omitted unavailable legacy fields
- Reference: `docs/superpowers/specs/2026-04-28-nwis-crosswalk-shapefile-field-names-design.md`
  - source of truth for the field list and behavior

## Implementation Notes

- Do not add commit steps to this plan. The user wants to handle commits manually.
- Do not change the `add-data` CSV header behavior in this plan; that work is out of scope here.
- Keep shapefile geometry in the `.shp` as it works today. The new work is about DBF field naming and selection.

## Task 1: Lock The NWIS Crosswalk Contract With Failing Tests

**Files:**
- Modify: `tests/test_waterdata_toolbox_demo_package.py`
- Reference: `src/waterdata_toolbox_demo/exports.py`

- [ ] **Step 1: Replace the reduced-schema shapefile test with a NWIS crosswalk expectation**

Update `test_export_station_shapefile_artifacts_reduce_fields` so it no longer expects:

```python
[
    "site_no",
    "loc_id",
    "stn_name",
    "site_tp",
    "state_cd",
    "county_cd",
    "lat",
    "lon",
    "agency_cd",
    "huc_code",
]
```

Instead, build a representative GeoDataFrame with raw monitoring-location fields such as:

- `agency_code`
- `monitoring_location_number`
- `monitoring_location_name`
- `site_type_code`
- `district_code`
- `state_code`
- `county_code`
- `country_code`
- `altitude`
- `altitude_accuracy`
- `altitude_method_code`
- `vertical_datum`
- `hydrologic_unit_code`
- `basin_code`
- `construction_date`
- `drainage_area`
- `contributing_drainage_area`
- `time_zone_abbreviation`
- `uses_daylight_savings`
- `national_aquifer_code`
- `aquifer_code`
- `aquifer_type_code`
- `well_constructed_depth`
- `hole_constructed_depth`
- `depth_source_code`
- `geometry`

Assert that the written DBF field names match the spec’s NWIS-style 10-character names, including `dec_lat_va` and `dec_long_v`.

- [ ] **Step 2: Add a failing test for derived coordinate attributes**

Add a focused test that writes one point feature and asserts:

- the DBF contains `dec_lat_va`
- the DBF contains `dec_long_v`
- the first record values match the point geometry coordinates

Use a concrete point like:

```python
Point(-82.1765, 32.0771388888889)
```

and assert the DBF values reflect:

```python
32.0771388888889
-82.1765
```

- [ ] **Step 3: Add a failing test for collision validation**

Add a small unit-style test around the field-name builder that monkeypatches or feeds a contrived crosswalk with two NWIS aliases that would still collide after 10-character truncation, and assert the exporter raises a clear `ValueError`.

Example shape:

```python
with pytest.raises(ValueError, match="collide after 10-character truncation"):
    ...
```

This pins down the “fail fast” rule and prevents the old `_1`, `_2` behavior from coming back.

- [ ] **Step 4: Run the focused shapefile tests to confirm red**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "shapefile or create_project" -v
```

Expected: FAIL because the code still emits the reduced schema and still uses suffix-based duplicate handling.

## Task 2: Replace The Generic Raw-Name Logic With A Code-Local Crosswalk

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Add one explicit crosswalk constant**

Near the top of `exports.py`, add a single source-of-truth structure for the exported shapefile attributes. Use the Water Data source field name plus its NWIS alias, for example:

```python
_STATION_SHAPEFILE_CROSSWALK = [
    ("agency_code", "agency_cd"),
    ("monitoring_location_number", "site_no"),
    ("monitoring_location_name", "station_nm"),
    ("site_type_code", "site_tp_cd"),
    ("district_code", "district_cd"),
    ("state_code", "state_cd"),
    ("county_code", "county_cd"),
    ("country_code", "country_cd"),
    ("horizontal_position_method_code", "coord_meth_cd"),
    ("horizontal_positional_accuracy", "coord_acy_cd"),
    ("original_horizontal_datum", "coord_datum_cd"),
    ("altitude", "alt_va"),
    ("altitude_method_code", "alt_meth_cd"),
    ("altitude_accuracy", "alt_acy_va"),
    ("vertical_datum", "alt_datum_cd"),
    ("hydrologic_unit_code", "huc_cd"),
    ("basin_code", "basin_cd"),
    ("construction_date", "construction_dt"),
    ("drainage_area", "drain_area_va"),
    ("contributing_drainage_area", "contrib_drain_area_va"),
    ("time_zone_abbreviation", "tz_cd"),
    ("uses_daylight_savings", "local_time_fg"),
    ("national_aquifer_code", "nat_aqfr_cd"),
    ("aquifer_code", "aqfr_cd"),
    ("aquifer_type_code", "aqfr_type_cd"),
    ("well_constructed_depth", "well_depth_va"),
    ("hole_constructed_depth", "hole_depth_va"),
    ("depth_source_code", "depth_src_cd"),
]
```

Do not include unavailable legacy fields. Keep geometry-derived coordinate fields out of this list for the moment; they should be handled in a dedicated derivation step.

- [ ] **Step 2: Replace `_raw_station_attribute_columns(...)` with crosswalk-driven selection**

Remove the current “every non-excluded column is eligible” logic. Replace it with a helper that:

- starts from `_STATION_SHAPEFILE_CROSSWALK`
- keeps only source fields that are present in the frame
- builds a stable ordered export field list

This is the key shift from “whatever raw fields are there” to “only the fields we intentionally crosswalk.”

- [ ] **Step 3: Replace `_truncate_shapefile_field_names(...)` with NWIS-alias truncation plus validation**

Delete the current suffix-based algorithm. Replace it with helpers that:

- truncate an NWIS alias to the first 10 characters
- collect all resulting field names
- raise a clear `ValueError` if any duplicates remain

Keep the error message explicit enough to tell which source fields or aliases collided.

- [ ] **Step 4: Run the new unit-style collision test**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "collision" -v
```

Expected: PASS once the old suffix behavior is gone and collisions raise.

## Task 3: Derive Legacy Coordinate Fields And Build The Final DBF Schema

**Files:**
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Reference: `src/waterdata_toolbox_demo/station_discovery.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Add a helper that derives `dec_lat_va` and `dec_long_va` from geometry**

Add a small helper in `exports.py` that takes one geometry value and returns:

```python
{
    "dec_lat_va": <y coordinate>,
    "dec_long_va": <x coordinate>,
}
```

Reuse the existing point extraction rules from `_geometry_xy(...)` so the geometry handling stays consistent.

- [ ] **Step 2: Merge geometry-derived coordinate fields into the export payload**

When building the station attribute export rows, append two synthetic attributes:

- `dec_lat_va`
- `dec_long_va`

Treat their NWIS aliases as their own final field names before the 10-character cut:

- `dec_lat_va` -> `dec_lat_va`
- `dec_long_va` -> `dec_long_v`

This keeps compatibility while still honoring the 10-character DBF limit.

- [ ] **Step 3: Update `_station_shapefile_field_specs(...)` to operate on the crosswalked schema**

Make `_station_shapefile_field_specs(...)` build specs from:

- selected raw crosswalk fields
- derived coordinate fields

For each field spec, store enough information to write rows without ambiguity:

```python
{
    "source_name": "monitoring_location_number",
    "field_name": "site_no",
    "field_type": "C",
    "field_size": 254,
    "field_decimal": 0,
}
```

For derived coordinate fields, include a clear marker such as:

```python
"derived_from": "geometry"
```

or an equivalent explicit mechanism.

- [ ] **Step 4: Update `_write_station_shapefile(...)` to use the new spec model**

Change the record-writing path so it no longer indexes into arbitrary frame columns only. Instead:

- read direct values from row data for crosswalked fields
- compute derived coordinate values from geometry for the synthetic coordinate fields
- pass each value through `_dbf_safe_value(...)`

Keep the point geometry writing path unchanged apart from reusing the same coordinate extraction helper.

- [ ] **Step 5: Run the focused shapefile tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "shapefile or create_project" -v
```

Expected: PASS

## Task 4: Keep Station Discovery Compatible And Remove No-Longer-Needed Code

**Files:**
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Verify `station_discovery.py` still passes the fields needed by the crosswalk**

Review `_normalize_station_frame(...)` and `_to_station_geodataframe(...)` to confirm the filtered frame retains the Water Data source columns used by the crosswalk.

Keep the existing geometry-construction fallback from `latitude` / `longitude` and `dec_lat_va` / `dec_long_va` only if it is still needed for tests or non-GeoJSON inputs. Do not add new normalization aliases here.

- [ ] **Step 2: Remove helper code that only existed for the old naming path**

Delete or rewrite logic in `exports.py` that is no longer meaningful once the new crosswalk is in place, especially:

- `_raw_station_attribute_columns(...)`
- `_truncate_shapefile_field_names(...)`
- comments/docstrings that describe raw-name preservation or `_1`, `_2` suffix fallback

Keep DBF-safe conversion, field type inference, and shapefile sidecar writing intact.

- [ ] **Step 3: Run the full package test file**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -v
```

Expected: PASS

## Task 5: Update The Field Note And Package Docs

**Files:**
- Modify: `docs/create-new-project-shapefile-fields.md`
- Modify: `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md`
- Optional: `README.md` if it mentions the old reduced schema or duplicate suffix behavior
- Test: `tests/test_waterdata_toolbox_demo_package.py`

- [ ] **Step 1: Rewrite the shapefile field note around the crosswalk**

Update `docs/create-new-project-shapefile-fields.md` so it no longer describes the old reduced schema. It should instead explain:

- the shapefile uses NWIS-style field names
- those names come from a code-local Water Data -> NWIS crosswalk
- names are then cut to 10 characters for shapefile DBF compatibility
- `dec_lat_va` and `dec_long_va` are retained from geometry
- unavailable legacy fields are omitted

- [ ] **Step 2: Update package docs if they mention the old reduced schema or suffix truncation**

Search `src/waterdata_toolbox_demo/waterdata-package-cli-gui.md` and `README.md` for any language that still implies:

- reduced 10-field shapefile schema
- raw-field suffix fallback

Replace that language with the NWIS crosswalk explanation if needed.

- [ ] **Step 3: Update doc assertions in the package test file**

Adjust any doc-content assertions in `test_package_build_docs_describe_cli_only_shapefile_app` so they reflect the new documentation language.

- [ ] **Step 4: Run the doc-related package tests**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -k "package_build_docs" -v
```

Expected: PASS

## Final Verification

- [ ] **Step 1: Run the full package test suite**

Run:

```bash
/Users/lludden/miniforge3/envs/nhm/bin/python -m pytest tests/test_waterdata_toolbox_demo_package.py -v
```

Expected: PASS

- [ ] **Step 2: Run one create-new-project shapefile smoke test**

Run:

```bash
PYTHONPATH=src /Users/lludden/miniforge3/envs/nhm/bin/python -m waterdata_toolbox_demo create-new-project --discharge --output-dir dist/outputs/cli_shp_smoke
```

Expected:

- `dist/outputs/cli_shp_smoke/discharge.shp` exists
- companion files `.dbf`, `.shx`, `.prj`, `.cpg` exist
- DBF field names follow the NWIS crosswalk output rather than the old reduced schema or `_1`, `_2` suffixes

- [ ] **Step 3: Stop for user review**

Do not commit. Summarize:

- which files changed
- whether tests passed
- whether the smoke export succeeded
- any remaining edge cases, especially around crosswalk collisions or missing geometry
