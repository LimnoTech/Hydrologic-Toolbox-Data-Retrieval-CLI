# CLI GW Workflow Names Design

## Summary

Rename the user-facing groundwater workflow names in the CLI from `daily` and `periodic` back to `gw_daily` and `gw_periodic`.

## Goals

- Make the CLI workflow names match the actual workflow/data type names used in the code
- Keep `discharge` unchanged
- Update both command families:
  - `create-new-project --wf ...`
  - `add-data ...`

## Final CLI Contract

`create-new-project` should accept:
- `--wf discharge`
- `--wf gw_daily`
- `--wf gw_periodic`

`add-data` should accept:
- `discharge`
- `gw_daily`
- `gw_periodic`

## Non-Goals

- Do not keep `daily` or `periodic` as compatibility aliases
- Do not rename internal workflow ids away from `gw_daily` and `gw_periodic`
- Do not change output file stems unless they already follow the internal names

## Implementation Direction

- Simplify the CLI parser so it accepts the internal workflow ids directly
- Remove the old alias mapping from `daily -> gw_daily` and `periodic -> gw_periodic`
- Update README and sandbox CLI notes to show the new names
- Update local CLI tests to assert the new accepted values and reject the old aliases
