# CLI-Only Shapefile Workflows Design

## Goal

Turn the packaged Windows app into a CLI-only executable. `create-new-project` should accept one or more workflow flags and write one shapefile per selected workflow. `add-data` should keep a simpler flag surface and continue writing the current custom CSV output.

## Approved Decisions

- The packaged `.exe` is CLI-only.
- The GUI module and its internal logic stay in the repo, but the packaged executable no longer routes into the GUI path.
- Launching the `.exe` with no arguments prints help and exits.
- The top-level interface uses subcommands:
  - `create-new-project`
  - `add-data`
- `create-new-project` accepts one or more human-facing workflow flags:
  - `--discharge`
  - `--daily`
  - `--periodic`
- `--daily` maps to the current `gw_daily` workflow.
- `--periodic` maps to the current `gw_periodic` workflow.
- `--bbox` remains supported for `create-new-project`, but it is optional and falls back to the current configured default when omitted.
- `add-data` uses the same workflow flags, but exactly one may be selected at a time.
- `create-new-project` writes shapefiles instead of CSV files.
- A short markdown note under `docs/` will explain which fields were excluded from the shapefile schema and why.

## CLI Contract

### Create New Project

```text
waterdata_toolbox_demo.exe create-new-project [--bbox WEST SOUTH EAST NORTH] [--discharge] [--daily] [--periodic] [--output-dir DIR]
```

Rules:

- At least one of `--discharge`, `--daily`, or `--periodic` is required.
- Multiple workflow flags may be combined in one call.
- If `--bbox` is omitted, the command uses the configured default bounding box.

Example:

```text
waterdata_toolbox_demo.exe create-new-project --discharge --daily --output-dir outputs
```

### Add Data

```text
waterdata_toolbox_demo.exe add-data [--discharge | --daily | --periodic] [--station-id ID] [--parameter-code CODE] [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD] [--output-dir DIR]
```

Rules:

- Exactly one workflow flag is required.
- `station-id`, `parameter-code`, and date arguments may still default from the current config when omitted.

Example:

```text
waterdata_toolbox_demo.exe add-data --discharge --station-id 02225500 --parameter-code 00060 --output-dir outputs
```

## Output Contract

### Create New Project

Each selected workflow writes one point shapefile set:

- `discharge.shp`
- `daily.shp`
- `periodic.shp`

Each shapefile output includes the normal sidecar files produced by the driver:

- `.shp`
- `.shx`
- `.dbf`
- `.prj`
- `.cpg`

Geometry is written as EPSG:4326 points.

### Add Data

`add-data` keeps the current CSV contract:

- daily workflows preserve the metadata preamble
- the body stays reduced to the approved CSV columns

## Shapefile Schema

The shapefile export uses a reduced schema rather than the full station-discovery CSV schema. This avoids shapefile field-name truncation, duplicate alias fields, and low-value metadata clutter.

Recommended fields:

- `site_no`
- `loc_id`
- `stn_name`
- `site_tp`
- `state_cd`
- `county_cd`
- `lat`
- `lon`
- `agency_cd`
- `huc_code`

Excluded fields fall into these groups:

- long descriptive duplicates already represented by the kept fields
- raw alias columns that map into the reduced schema
- accuracy/datum/revision metadata that is not central to the shapefile use case
- workflow or helper columns that the shapefile itself makes redundant
- groundwater construction and similar fields that do not add much value to the station-discovery shapefile

The separate docs note will enumerate the excluded columns and explain these reductions explicitly.

## Runtime and Packaging Changes

- Keep the GUI code in the repo, but remove the GUI route from the packaged app entrypoint.
- Stop advertising GUI usage in the package-facing docs.
- Remove GUI-specific executable messaging from the packaged runtime path.
- Keep the CLI as the only runtime path for the packaged app.

## Error Handling

- If no workflow flags are passed to `create-new-project`, show a clear parser error.
- If more than one workflow flag is passed to `add-data`, show a clear parser error.
- If shapefile writing fails, surface the workflow name and destination path in the error message.
- If required geometry columns are missing or invalid, fail with a targeted export error rather than silently writing empty geometry.

## Verification

- Parser tests for the new workflow flag surface.
- CLI smoke tests for:
  - `create-new-project --discharge`
  - `create-new-project --discharge --daily`
  - `add-data --discharge`
- Export tests confirming shapefile outputs per selected workflow.
- Docs checks confirming the packaged app is described as CLI-only and that the field-reduction note exists under `docs/`.
