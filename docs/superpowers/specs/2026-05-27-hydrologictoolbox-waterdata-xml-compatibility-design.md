# HydrologicToolbox Water Data XML Compatibility Design

## Goal

Add a HydrologicToolbox XML compatibility entrypoint to
`waterdata_toolbox_demo` that:

1. accepts NWIS/Water Data XML requests for station discovery and time-series
   retrieval
2. executes those requests using the current Water Data-based workflow logic
3. returns XML success or error strings that HydrologicToolbox can consume

For HydrologicToolbox integration, this XML contract is the expected calling
surface. The current simple CLI must still remain available and unchanged for
direct use.

## Current State

- `create-new-project` currently accepts:
  - one or more `--wf` values
  - a WGS84 latitude/longitude `--bbox`
  - an `--output-dir`
- `add-data` currently accepts:
  - exactly one workflow
  - exactly one `--station-id`
  - a date range
  - an `--output-dir`
- The app currently prints summary lines and file paths to stdout and returns
  exit code `0` on success.
- Station shapefiles are currently written in WGS84 / `EPSG:4326`.
- There is no XML request parser, XML response formatter, projected input bbox
  support, projected shapefile output support, or multi-station `add-data`
  support.

## Confirmed Assumptions

- HydrologicToolbox will keep splitting unrelated non-Water-Data requests, such
  as MRLC/NLCD or map-tile work, on its side.
- The incoming XML should be treated as a superset envelope.
  - Extra tags may be present.
  - Unsupported but harmless tags should be ignored instead of causing errors.
- Projection strings are sufficient for the first compatibility pass.
  - EPSG-code input support is out of scope for now.
- If `DesiredProjection` is omitted, output should default to WGS84 /
  `EPSG:4326`.
- `SaveIn` is required.
  - If it is missing, the tool should return an XML error.
- Multiple station requests should write multiple output files.
- Failures should return an `<error>...</error>` XML string.

## Requirements

1. Preserve the existing direct CLI contract.
   - Do not replace `create-new-project` or `add-data`.
2. Add one XML compatibility entrypoint that accepts the HydrologicToolbox XML
   request shape for the NWIS/Water Data subset.
3. Support both compatibility flows:
   - station discovery / shapefile export
   - add-data / CSV export
4. Accept a superset XML shape and ignore irrelevant tags when possible.
5. Validate a required subset of tags per operation and return XML errors for
   missing required values.
6. Support projected input region coordinates through projection strings in the
   XML `<region>` block.
7. Reproject station shapefile outputs to `DesiredProjection` when present.
8. Default station shapefile outputs to WGS84 / `EPSG:4326` when
   `DesiredProjection` is missing.
9. Support multiple workflows for station discovery.
10. Support multiple station IDs for add-data.
11. Return XML success strings that enumerate the files written.

## Recommended Approach

Add a HydrologicToolbox XML compatibility layer on top of the existing workflow
modules instead of rewriting the current CLI.

This compatibility layer should:

- parse HydrologicToolbox-style XML into a normalized internal request model
- dispatch to the same `station_discovery.py`, `timeseries.py`, and
  `exports.py` workflow logic already used by the simple CLI
- transform projected input bboxes into WGS84 before Water Data API calls
- optionally reproject output shapefiles before writing
- format XML success/error strings for HydrologicToolbox consumption

This keeps the existing CLI clean and stable while adding the required
HydrologicToolbox-facing integration surface.

## Design

### Compatibility entrypoint

Add one new HydrologicToolbox-oriented entrypoint to the CLI surface rather
than changing the existing commands.

Recommended behavior:

- Keep `create-new-project` and `add-data` exactly as they are for direct use.
- Add a new XML-driven mode, for example:
  - `xml-compat`
  - or another clearly named compatibility command

That mode should:

- accept one XML request payload
- parse the `<function>` name and `<arguments>` block
- decide whether the request maps to station discovery or add-data
- emit one XML string to stdout
  - `<success>...</success>` on success
  - `<error>...</error>` on failure

This XML entrypoint is the adapter layer HydrologicToolbox should call. It does
not replace the existing simple CLI for direct/manual use.

### XML envelope strategy

Treat the incoming XML as a broad envelope and then extract only the subset
needed for the Water Data operation being executed.

Implications:

- The parser should not require every tag in the XML.
- The parser should not reject a request simply because unrelated tags are
  present.
- The parser should validate only the required subset for the selected Water
  Data operation.

Examples:

- `SaveIn` is required because output writing cannot proceed without it.
- `DesiredProjection` is optional because there is a defined default.
- `CacheFolder`, `clip`, `merge`, or `joinattributes` may appear but can be
  ignored in the first pass if they do not affect the Water Data work.

### Supported XML functions

The first compatibility pass should support the NWIS/Water Data station and
timeseries functions needed by HydrologicToolbox.

At minimum:

- station discovery equivalent to the old `GetNWISStations`
- add-data equivalent to the old discharge / groundwater retrieval requests

The compatibility layer should map XML function names into the existing modern
workflow names:

- `discharge`
- `gw_daily`
- `gw_periodic`

For station discovery, the XML request may include multiple `DataType` tags.
Each recognized workflow should produce one shapefile output.

For add-data, the compatibility layer should accept one or more station IDs and
produce one file per station per requested workflow.

### Required and optional tags

The compatibility layer should define operation-specific required subsets.

#### Station discovery required subset

- function name that maps to station discovery
- `SaveIn`
- `<region>` with:
  - `northbc`
  - `southbc`
  - `eastbc`
  - `westbc`
  - `projection`
- at least one `DataType`

#### Station discovery optional subset

- `DesiredProjection`
- `CacheFolder`
- `MinCount`
- `clip`
- `merge`
- `HUC8`

#### Add-data required subset

- function name that maps to a supported add-data operation
- `SaveIn`
- at least one `stationid`

#### Add-data optional subset

- `DesiredProjection`
  - parsed but ignored for CSV output in the first pass
- `CacheFolder`
- `GetEvenIfCached`
- `MinCount`
- `clip`
- `merge`
- `joinattributes`
- `<region>` block
  - may be present in the envelope but is not required for Water Data
    timeseries retrieval

### Projection handling

#### Input region projection

For station discovery compatibility requests, the incoming `<region>` block
contains projected coordinate bounds plus a matching projection string.

The compatibility layer should:

1. parse the projected bbox values from `<region>`
2. parse the `<region><projection>` string
3. transform that bbox into WGS84 latitude/longitude
4. pass the transformed WGS84 bbox into the existing Water Data discovery logic

This is required because the modern Water Data calls expect a WGS84-style bbox,
while the old XML caller may supply projected coordinates.

#### Output projection

For station discovery shapefile outputs:

- if `DesiredProjection` is present:
  - reproject the station GeoDataFrame to that projection before writing the
    shapefile
  - write a matching `.prj`
- if `DesiredProjection` is missing:
  - keep current behavior and write WGS84 / `EPSG:4326`

This compatibility behavior applies only to the XML adapter flow. The existing
simple CLI may continue using its current WGS84-only output behavior unless
explicitly enhanced later.

### Station discovery compatibility flow

For a station discovery XML request:

1. Parse the XML envelope.
2. Extract:
   - one or more `DataType` values
   - `SaveIn`
   - `DesiredProjection` if present
   - projected `<region>` bounds
   - `<region><projection>`
3. Transform the input region bbox to WGS84.
4. Run station discovery once per requested workflow using the current Water
   Data logic.
5. Reproject each output GeoDataFrame to `DesiredProjection` if provided.
6. Write one shapefile set per workflow.
7. Return a success XML string listing the shapefile paths.

Recommended success shape:

```xml
<success>
  <add_shape workflow="discharge">C:\path\NWIS_Stations_discharge.shp</add_shape>
  <add_shape workflow="gw_daily">C:\path\NWIS_Stations_gw_daily.shp</add_shape>
  <add_shape workflow="gw_periodic">C:\path\NWIS_Stations_gw_periodic.shp</add_shape>
</success>
```

The XML shape should be close to what HydrologicToolbox already understands,
while still being explicit about workflow names.

### Add-data compatibility flow

For an add-data XML request:

1. Parse the XML envelope.
2. Extract:
   - one or more station IDs
   - the relevant workflow or workflows
   - `SaveIn`
   - date-range fields if present
3. Ignore unrelated envelope fields that do not affect Water Data retrieval.
4. Run the current Water Data timeseries workflow once per station per workflow.
5. Write one CSV per station/workflow combination.
6. Return a success XML string listing the data-file paths.

The compatibility layer should support multiple stations in one request. It
does not need to combine them into one file.

Recommended success shape:

```xml
<success>
  <add_data type="CSV" subtype="discharge" stationid="02336106">C:\path\discharge_02336106.csv</add_data>
  <add_data type="CSV" subtype="gw_daily" stationid="324209082430201">C:\path\gw_daily_324209082430201.csv</add_data>
</success>
```

The XML should truthfully describe the actual output format rather than
pretending the CSV is an old NWIS RDB file.

### Error handling

Compatibility mode should always prefer an XML error payload over a silent
failure.

Recommended error shape:

```xml
<error>Missing required tag: SaveIn</error>
```

Examples of compatibility errors:

- missing `SaveIn`
- missing `<region>` fields for station discovery
- missing station IDs for add-data
- unsupported `DataType`
- unsupported function name
- invalid projection string
- invalid bbox transformation
- output directory creation failure
- Water Data request failure

The compatibility layer should:

- return a nonzero process exit code on failure
- emit `<error>...</error>` on stdout or stderr according to the chosen CLI
  contract
- avoid partial success XML mixed with raw Python tracebacks

### Output naming

The compatibility mode should keep naming predictable and stable.

Recommended first-pass rule:

- reuse the current file naming conventions where practical
- return the exact saved paths in the XML success payload

This avoids blocking the compatibility layer on perfect imitation of old D4EM
filenames, while still giving HydrologicToolbox an authoritative path list to
consume.

### Internal architecture

The implementation should introduce a small XML adapter layer rather than
embedding XML parsing logic inside the current workflow modules.

Suggested responsibility split:

- `cli.py`
  - expose the compatibility entrypoint
  - route XML mode into an XML adapter
- new XML adapter module
  - parse XML
  - validate required subsets
  - map XML requests into internal workflow calls
  - format XML success/error responses
- `station_discovery.py`
  - remain the station discovery executor
- `timeseries.py`
  - remain the timeseries executor
- `exports.py`
  - own file writing, plus any needed projection-aware shapefile export support

This keeps the XML contract isolated from the direct CLI contract.

### Testing

Add coverage for:

- XML parsing of a superset envelope
- ignored extra tags
- missing required tags
- `<error>...</error>` formatting
- defaulting `DesiredProjection` to WGS84
- projected region bbox transformation into WGS84 request coordinates
- multi-workflow station discovery XML requests
- multi-station add-data XML requests
- success XML payload formatting for station outputs
- success XML payload formatting for add-data outputs
- station shapefile reprojection when `DesiredProjection` is present
- preservation of the existing simple CLI behavior

At least one integration-style test should verify:

- one station discovery XML request with multiple `DataType` values
- one add-data XML request with multiple station IDs
- XML output paths match files actually written

## Out of Scope

- Splitting MRLC/NLCD or other unrelated provider requests
- Replacing the simple direct CLI
- Supporting EPSG-code projection inputs in the first pass
- Reproducing old D4EM caching behavior
- Returning map tiles or non-Water-Data products
- Combining multiple stations into one CSV output file
- Perfectly reproducing every old D4EM filename or XML attribute
- Reintroducing legacy NWIS RDB files instead of the approved CSV outputs
