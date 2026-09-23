# Waterdata Demo Plots Design

## Goal

Add a simple interactive plotting section to the USGS waterdata demo notebook so users can switch between the generated `discharge`, `gw_daily`, and `gw_periodic` outputs and view a matplotlib time-series plot for the selected workflow.

## Context

The notebook already:

- demonstrates the notebook-first `dataretrieval.waterdata` API usage
- recreates the legacy `Creating New Project` and `Adding Data to Project` sections
- writes JSON, CSV, and parquet outputs for the three workflow types

The new plotting feature should build on those generated outputs instead of adding any new retrieval path.

## Requirements

- Add a new notebook section named `Plot Generated Outputs`
- Reuse the existing `add_data_results` from the `Adding Data to Project` section
- Use `matplotlib` for plotting
- Use a simple `ipywidgets` selector to choose `discharge`, `gw_daily`, or `gw_periodic`
- Plot the selected workflow using its generated output data
- Keep the plotting logic inside the notebook, consistent with the notebook-first demo approach
- Assume `ipywidgets` is available; no fallback path is needed

## Data Shape Assumptions

The current exported outputs for all three workflow types already share the columns needed for a common plotting path:

- `time`
- `value`
- `unit_of_measure`
- `workflow_type`

This allows the notebook to use one plotting helper for all three workflow types.

## Recommended Approach

Add a notebook-local plotting section after the `Adding Data to Project` render cell.

This section should:

1. import `matplotlib.pyplot as plt` and `ipywidgets as widgets`
2. define a small helper that prepares the selected payload for plotting
3. define a plotting function that renders `value` against `time`
4. define a widget renderer that exposes a single dropdown for workflow selection
5. render the widget using the previously generated `add_data_results`

This keeps the feature simple, visible, and easy to explain in the demo notebook.

## Notebook Changes

### Imports

Extend the notebook imports to include:

- `import matplotlib.pyplot as plt`
- `import ipywidgets as widgets`
- `from IPython.display import clear_output`

### New Markdown Section

Add a short markdown section:

- heading: `## Plot Generated Outputs`
- brief note that the plot is driven by the same generated outputs created in the prior section

### New Plot Helpers

Add notebook-local helpers such as:

- `_prepare_plot_frame(payload)`
  - takes the selected workflow payload
  - copies the frame
  - converts `time` from epoch milliseconds to pandas datetimes
  - sorts rows by `time`
  - returns a plot-ready frame

- `plot_generated_output(workflow_type, add_data_results)`
  - looks up the selected workflow result
  - handles missing or empty payloads with a short message
  - plots `value` against `time`
  - uses `unit_of_measure` for the y-axis label when available
  - uses a readable title derived from the workflow name

- `render_plot_selector(add_data_results)`
  - builds a `widgets.Dropdown`
  - exposes the three workflow types
  - redraws the matplotlib figure when selection changes

## Plot Behavior

- x-axis: parsed `time`
- y-axis: `value`
- plot style: simple line with markers
- title: selected workflow label plus station id when available
- y-axis label: `Value (<unit>)` when `unit_of_measure` exists, otherwise `Value`
- grid: enabled for readability

## Testing

Update notebook tests to verify:

- the notebook imports `matplotlib.pyplot` and `ipywidgets`
- the notebook contains a `Plot Generated Outputs` section
- notebook-local plotting helpers exist
- the plot render cell uses `add_data_results`
- the plotting helpers can prepare a frame with parsed datetimes and render against the selected workflow

Keep existing retrieval and export tests unchanged unless the notebook structure shift requires small updates.

## Verification

After implementation:

- execute the notebook with `jupyter`, `matplotlib`, `ipywidgets`, `dataretrieval`, and `pyarrow`
- rerun `tests/test_usgs_waterdata_demo.py`
- confirm that the interactive plot section appears in the executed notebook and still preserves the existing generated artifacts

## Out of Scope

- multi-select plotting
- y-column selection
- custom styling controls
- plot export buttons
- changes to the generated JSON, CSV, or parquet schemas
- additional retrieval calls beyond the current notebook workflow
