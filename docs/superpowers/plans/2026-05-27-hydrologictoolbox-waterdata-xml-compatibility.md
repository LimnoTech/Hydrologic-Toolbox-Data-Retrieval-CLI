# HydrologicToolbox Water Data XML Compatibility Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a HydrologicToolbox-facing XML entrypoint that accepts NWIS/Water Data XML requests, executes station discovery or add-data through the existing workflow logic, supports projected station-discovery regions and projected shapefile output, and returns XML success/error strings.

**Architecture:** Introduce a thin XML adapter layer that lives between the CLI and the existing workflow modules. The adapter parses a superset XML envelope, validates only the required subset for the requested Water Data function, transforms projected station-discovery regions into WGS84 for API calls, optionally reprojects output station shapefiles to `DesiredProjection`, and formats XML success/error responses. Keep the direct `create-new-project` and `add-data` CLI unchanged for manual use.

**Tech Stack:** Python, argparse, xml.etree.ElementTree, pathlib, pandas, geopandas, pyproj, dataretrieval.waterdata, pytest

---

## File Map

**Create:**
- `src/waterdata_toolbox_demo/xml_compat.py`
  - XML parsing, request validation, request normalization, workflow dispatch, and XML response formatting
- `tests/test_xml_compat.py`
  - focused offline coverage for XML parsing, validation, projection handling, and XML response formatting

**Modify:**
- `src/waterdata_toolbox_demo/cli.py`
  - add the HydrologicToolbox XML entrypoint while preserving the existing direct CLI
- `src/waterdata_toolbox_demo/station_discovery.py`
  - allow station discovery export to honor a requested output projection without changing the direct CLI contract
- `src/waterdata_toolbox_demo/exports.py`
  - support projection-aware station shapefile writing and `.prj` generation for XML-driven station discovery
- `src/waterdata_toolbox_demo/timeseries.py`
  - expose or adapt a path for multi-station add-data orchestration driven by the XML layer
- `README.md`
  - add a short note that HydrologicToolbox integration uses the XML entrypoint while the simple CLI remains available for manual use

**Reference:**
- `docs/superpowers/specs/2026-05-27-hydrologictoolbox-waterdata-xml-compatibility-design.md`

## Implementation Notes

- Keep the existing direct CLI exactly as-is:
  - `create-new-project`
  - `add-data`
- Add a new XML-driven entrypoint for HydrologicToolbox, for example `xml-compat`.
- Treat the XML input as a superset envelope:
  - ignore irrelevant tags
  - validate only the required subset for the selected operation
- Required XML behaviors:
  - missing `SaveIn` -> `<error>...</error>`
  - missing required station-discovery region tags -> `<error>...</error>`
  - missing station IDs for add-data -> `<error>...</error>`
  - missing `DesiredProjection` -> default output shapefiles to WGS84 / `EPSG:4326`
- Station discovery XML requests may include multiple `DataType` tags.
- Add-data XML requests may include multiple station IDs and should write one file per station per workflow.
- Do not design for EPSG-code projection input in the first pass; projection strings are enough.
- The XML adapter should be isolated in its own module instead of spreading XML parsing logic into the workflow files.

## Task 1: Add a failing XML adapter test module

**Files:**
- Create: `tests/test_xml_compat.py`
- Reference: `src/waterdata_toolbox_demo/cli.py`
- Reference: `docs/superpowers/specs/2026-05-27-hydrologictoolbox-waterdata-xml-compatibility-design.md`

- [ ] **Step 1: Create the XML compatibility test module**

Create:

```text
tests/test_xml_compat.py
```

- [ ] **Step 2: Add one failing parser-surface test for the new CLI entrypoint**

Write a test that asserts the CLI parser accepts the new XML entrypoint name and
the required XML payload input flag or positional input once that contract is
chosen.

Keep the assertion specific:

```python
def test_parser_accepts_xml_compat_command():
    from waterdata_toolbox_demo.cli import build_parser

    args = build_parser().parse_args(["xml-compat", "--xml", "<function />"])
    assert args.command == "xml-compat"
```

- [ ] **Step 3: Add one failing XML error-shape test**

Write a test that calls the future XML adapter with a request missing `SaveIn`
and asserts it returns:

```xml
<error>Missing required tag: SaveIn</error>
```

- [ ] **Step 4: Run the new XML tests to verify they fail**

Run:

```bash
python -m pytest tests/test_xml_compat.py -v
```

Expected:
- fail because the XML adapter and CLI entrypoint do not exist yet

## Task 2: Add the XML compatibility CLI entrypoint

**Files:**
- Modify: `src/waterdata_toolbox_demo/cli.py`
- Create: `src/waterdata_toolbox_demo/xml_compat.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Add the XML compatibility subcommand to the parser**

Add a new subcommand such as:

```python
xml_parser = subparsers.add_parser("xml-compat")
```

Give it a single clear XML input surface, for example:

```python
xml_parser.add_argument(
    "--xml",
    required=True,
    help="HydrologicToolbox NWIS/Water Data XML request string.",
)
```

Do not change the existing `create-new-project` or `add-data` parser contract.

- [ ] **Step 2: Add a dispatch branch in `run_cli(...)`**

Route the new command into a dedicated XML adapter function in a new module.

The branch should:

- call the XML adapter
- print exactly one XML string on success or failure
- return `0` on success
- return nonzero on failure

- [ ] **Step 3: Run the parser-surface tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "parser or command" -v
```

Expected:
- parser test passes
- XML behavior tests still fail because adapter logic is not implemented yet

## Task 3: Implement XML parsing and required-subset validation

**Files:**
- Create: `src/waterdata_toolbox_demo/xml_compat.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Add XML parsing helpers**

Implement small helpers that:

- parse the XML string with `xml.etree.ElementTree`
- extract the `<function>` name
- extract `<arguments>`
- read repeated tags such as:
  - `DataType`
  - `stationid`

Keep the parser forgiving about irrelevant tags.

- [ ] **Step 2: Add request-normalization helpers**

Create normalized request structures for:

- station discovery XML requests
- add-data XML requests

Each normalized structure should contain only the fields actually needed by the
Water Data operation.

- [ ] **Step 3: Add required-subset validation**

Implement validation helpers that return XML error strings for:

- missing `SaveIn`
- missing station-discovery `<region>` bounds
- missing station-discovery `<region><projection>`
- missing station IDs for add-data
- missing `DataType` for station discovery
- unsupported function names or workflow names

- [ ] **Step 4: Add focused failing tests for each validation rule**

Add parametrized tests that assert the exact `<error>...</error>` shape for the
validation failures above.

- [ ] **Step 5: Run the XML validation tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "error or validate or missing" -v
```

Expected:
- pass

## Task 4: Add projection parsing and station-discovery bbox transformation

**Files:**
- Modify: `src/waterdata_toolbox_demo/xml_compat.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Write a failing projection-transform test**

Add a test that provides:

- projected `northbc`, `southbc`, `eastbc`, `westbc`
- a projection string in `<region><projection>`

Then assert the adapter transforms that region into a WGS84 bbox tuple in:

```python
(west, south, east, north)
```

The test should verify the adapter sends WGS84-ready coordinates to the station
discovery layer.

- [ ] **Step 2: Implement projection-string transformation**

Use `pyproj` to:

- build a transformer from the XML region projection to WGS84
- transform the bbox corners
- derive a safe WGS84 request bbox

Raise or return `<error>...</error>` for invalid projection strings.

- [ ] **Step 3: Add default output projection behavior**

Normalize `DesiredProjection` so that:

- when present, it is stored for later shapefile reprojection
- when missing, it resolves to WGS84 / `EPSG:4326`

- [ ] **Step 4: Run the projection tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "projection or bbox" -v
```

Expected:
- pass

## Task 5: Add XML response formatting helpers

**Files:**
- Modify: `src/waterdata_toolbox_demo/xml_compat.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Write failing success-shape tests**

Add tests that expect:

```xml
<success>
  <add_shape workflow="discharge">...</add_shape>
</success>
```

and:

```xml
<success>
  <add_data type="CSV" subtype="gw_daily" stationid="...">...</add_data>
</success>
```

- [ ] **Step 2: Implement XML success/error formatters**

Add helpers for:

- one generic `<error>...</error>` formatter
- one station-discovery success formatter
- one add-data success formatter

Use the exact saved output paths in the XML body.

- [ ] **Step 3: Run the XML formatting tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "success or error or xml" -v
```

Expected:
- pass

## Task 6: Support projection-aware station shapefile export

**Files:**
- Modify: `src/waterdata_toolbox_demo/station_discovery.py`
- Modify: `src/waterdata_toolbox_demo/exports.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Write a failing projection-aware station export test**

Create a GeoDataFrame in WGS84 and assert that when a requested output
projection is supplied:

- the frame is reprojected before shapefile writing
- the `.prj` reflects the requested output projection instead of the hard-coded
  WGS84 text

- [ ] **Step 2: Update station export plumbing**

Extend the station export path so the XML adapter can supply an output
projection without changing the direct CLI behavior.

A safe shape is:

- keep direct CLI calls using the current default
- allow the XML adapter to pass an explicit projection argument into station
  export

- [ ] **Step 3: Replace the hard-coded `.prj` behavior for the XML path**

Update shapefile sidecar writing so:

- default behavior still writes WGS84 for the existing CLI path
- XML-driven station exports write a `.prj` that matches the requested output
  projection

- [ ] **Step 4: Run the station export projection tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "shapefile and projection" -v
```

Expected:
- pass

## Task 7: Implement station-discovery XML execution

**Files:**
- Modify: `src/waterdata_toolbox_demo/xml_compat.py`
- Reference: `src/waterdata_toolbox_demo/station_discovery.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Write a failing station-discovery execution test**

Stub the station-discovery executor and assert that:

- multiple `DataType` values are accepted
- the transformed WGS84 bbox is passed through
- `SaveIn` is used as the output directory
- the returned file paths are emitted in the `<success>` XML

- [ ] **Step 2: Implement workflow mapping for station discovery**

Map XML `DataType` values into internal workflow names:

- `discharge`
- `gw_daily`
- `gw_periodic`

- [ ] **Step 3: Implement station-discovery XML dispatch**

Connect the normalized XML request to the current station discovery orchestration
and then to the XML success formatter.

- [ ] **Step 4: Run the station-discovery XML tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "station and xml" -v
```

Expected:
- pass

## Task 8: Implement multi-station add-data XML execution

**Files:**
- Modify: `src/waterdata_toolbox_demo/xml_compat.py`
- Modify: `src/waterdata_toolbox_demo/timeseries.py`
- Test: `tests/test_xml_compat.py`

- [ ] **Step 1: Write a failing multi-station add-data execution test**

Stub the add-data executor and assert that:

- multiple `stationid` tags are accepted
- one file is written per station per workflow
- unrelated XML envelope fields are ignored
- the returned file paths are emitted in the `<success>` XML

- [ ] **Step 2: Add a small multi-station orchestration path**

Do not distort the single-station direct CLI path. Instead:

- keep `get_usgs_timeseries(...)` as the single-station worker
- let the XML adapter loop stations and collect results

Only add helper plumbing in `timeseries.py` if needed to keep the XML adapter
thin and the code readable.

- [ ] **Step 3: Implement add-data workflow mapping**

Support the recognized Water Data workflows needed by HydrologicToolbox and map
them into the current internal workflow names.

- [ ] **Step 4: Implement add-data XML dispatch**

Connect the normalized XML request to the multi-station add-data loop and then
to the XML success formatter.

- [ ] **Step 5: Run the add-data XML tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "add_data or stationid or multi" -v
```

Expected:
- pass

## Task 9: Add CLI-level XML integration coverage

**Files:**
- Modify: `tests/test_xml_compat.py`
- Reference: `src/waterdata_toolbox_demo/cli.py`

- [ ] **Step 1: Add one CLI-level station XML integration test**

Use a stubbed XML adapter or monkeypatched executor and assert:

- the new CLI command accepts XML input
- it prints `<success>...</success>` to stdout
- it returns `0`

- [ ] **Step 2: Add one CLI-level XML error integration test**

Assert:

- invalid XML or missing required tags produce `<error>...</error>`
- the CLI returns a nonzero exit code

- [ ] **Step 3: Run the CLI-level XML tests**

Run:

```bash
python -m pytest tests/test_xml_compat.py -k "cli and xml" -v
```

Expected:
- pass

## Task 10: Update the README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add one short HydrologicToolbox note**

Add a concise note that:

- the direct CLI remains available
- HydrologicToolbox integration uses the XML entrypoint

- [ ] **Step 2: Add one tiny XML usage example**

Document one compact example of:

- how the XML entrypoint is invoked
- that it returns XML success/error strings

Keep this short; do not turn the README into the full integration spec.

## Task 11: Full verification sweep

**Files:**
- Reference: `tests/test_xml_compat.py`
- Reference: `tests/test_cli_signature.py`

- [ ] **Step 1: Run the XML compatibility suite**

Run:

```bash
python -m pytest tests/test_xml_compat.py -v
```

Expected:
- pass

- [ ] **Step 2: Run the existing non-live CLI signature suite**

Run:

```bash
python -m pytest tests/test_cli_signature.py -k "not live" -q
```

Expected:
- pass

- [ ] **Step 3: Run one focused direct CLI regression**

Run:

```bash
python -m pytest tests/test_cli_signature.py::test_help_surface_for_create_new_project -v
```

Expected:
- pass

- [ ] **Step 4: Review stdout/stderr behavior manually**

Confirm:

- XML compatibility command prints only XML success/error payloads
- direct CLI commands still print the existing human-readable summaries

## Suggested Commit Sequence

- [ ] Commit 1: scaffold XML compatibility CLI surface and failing tests
- [ ] Commit 2: add XML parsing, validation, and XML response formatting
- [ ] Commit 3: add projected station-discovery XML execution and projection-aware shapefile export
- [ ] Commit 4: add multi-station add-data XML execution and README note
