# Water Data Sidecar Package

This sidecar package copies the current demo workflow logic into reusable Python modules without changing the existing notebook or `helpers/` module.

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

Launch the small desktop GUI by running the module with no arguments:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo
```

## Windows exe build

Build the `.exe` on Windows, not macOS. From a Windows environment with the project checked out:

```bash
pip install -e .[build]
pyinstaller waterdata_toolbox_demo.spec
```

The resulting executable will be written under `dist/`. The shared app entrypoint uses CLI mode when arguments are present and opens the GUI when launched without arguments.
