# Water Data ToolBox App

This package provides the same small Water Data ToolBox CLI and GUI app in a CSV-only form.

## Local package runs

From the repo root, use the `src/` layout directly:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo create-new-project
PYTHONPATH=src python -m waterdata_toolbox_demo add-data --workflow-type discharge
PYTHONPATH=src python -m waterdata_toolbox_demo
```

If you prefer an installed package workflow:

```bash
pip install -e .
python -m waterdata_toolbox_demo create-new-project
python -m waterdata_toolbox_demo add-data --workflow-type gw_daily
python -m waterdata_toolbox_demo
```

## CLI examples

Create New Project:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo create-new-project \
  --bbox -82.859 31.899 -82.013 32.947 \
  --workflow-type discharge \
  --workflow-type gw_daily
```

Adding Data to Project:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo add-data \
  --workflow-type gw_periodic \
  --station-id 410947071344803 \
  --parameter-code 72019 \
  --start-date 1880-01-01 \
  --end-date 2100-01-01 \
  --output-dir outputs/usgs_waterdata_demo
```

## GUI launch

Launch the desktop GUI by running the module with no arguments:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo
```

## CSV-only outputs

- `add-data` writes one CSV artifact per run.
- Daily workflows keep the custom metadata preamble:
  - `# site_no,Description,Parameter,Statistic,TS_ID,IV_TS_ID`
  - `Time,Daily values,Approval status,Qualifier`
- `create-new-project` writes one CSV artifact per selected workflow.

## Windows app build

Build the packaged Windows app on Windows, not macOS. From a Windows environment with the project checked out:

```bash
pip install -e .[build]
pyinstaller waterdata_toolbox_demo.spec
```

The default build emits an `onedir` app for faster startup. Launch the packaged app from:

```text
dist/waterdata_toolbox_demo/waterdata_toolbox_demo.exe
```

The shared app entrypoint still uses CLI mode when arguments are present and opens the GUI when launched without arguments.
