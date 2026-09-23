# CLI Signature Simplification Design

## Summary

The CLI should move away from the current three-boolean workflow flags (`--discharge`, `--daily`, `--periodic`) and adopt a more standard command signature:

- `create-new-project --wf discharge --wf daily`
- `add-data discharge --station-id 02225500 --parameter-code 00060`

This keeps multi-workflow selection explicit for `create-new-project` and makes `add-data` simpler by using a single positional workflow argument.

## Goals

- Make the CLI easier to understand from `--help` output alone.
- Remove the “exactly one of these three booleans” pattern from `add-data`.
- Use a more conventional multi-value option for `create-new-project`.
- Keep the actual workflow behavior unchanged.

## Non-Goals

- Changing workflow internals or Water Data retrieval logic.
- Changing output formats.
- Removing demo defaults unless explicitly approved later.

## Proposed Signature

### Create New Project

Replace:

```text
create-new-project --discharge --daily
```

with:

```text
create-new-project --wf discharge --wf daily
```

Behavior:

- `--wf` is repeatable
- allowed values are:
  - `discharge`
  - `daily`
  - `periodic`
- at least one workflow is required

### Add Data

Replace:

```text
add-data --discharge --station-id 02225500 --parameter-code 00060
```

with:

```text
add-data discharge --station-id 02225500 --parameter-code 00060
```

Behavior:

- workflow becomes one required positional argument
- allowed values are:
  - `discharge`
  - `daily`
  - `periodic`

## Internal Mapping

Human-facing workflow values should still map to the existing internal workflow ids:

- `discharge` -> `discharge`
- `daily` -> `gw_daily`
- `periodic` -> `gw_periodic`

This preserves current behavior while simplifying the CLI surface.

## Help And Usability Changes

The parser should add real `help=` text for:

- `--wf`
- `--bbox`
- `--station-id`
- `--parameter-code`
- `--start-date`
- `--end-date`
- `--output-dir`

The help output should make clear:

- `create-new-project` accepts one or more workflows
- `add-data` accepts exactly one workflow because it is positional
- bbox order is `WEST SOUTH EAST NORTH`

## Code Areas Affected

- `src/waterdata_toolbox_demo/cli.py`
  - replace boolean workflow flags
  - add repeatable `--wf` for `create-new-project`
  - add positional workflow for `add-data`
- tests covering parser behavior and CLI dispatch
- root README and any active CLI docs/examples

## Acceptance Criteria

- `create-new-project --wf discharge --wf daily` works
- `add-data discharge --station-id ... --parameter-code ...` works
- old boolean workflow flags are removed from the active CLI
- help output is clearer and more conventional

## Notes

This is a CLI surface simplification only. It intentionally keeps the existing internal workflow mapping and demo defaults unless a later change decides to tighten those too.
