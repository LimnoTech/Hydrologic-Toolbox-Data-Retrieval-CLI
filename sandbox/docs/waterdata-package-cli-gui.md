# Water Data ToolBox Package Notes

This package now supports a CLI-only packaged app workflow.

## Current App Behavior

- `create-new-project` writes shapefiles
- `add-data` writes CSV
- the packaged executable does not launch the GUI
- the GUI code still exists in the repo for reference and development

## Create New Project

Use one or more `--wf` selections:

- `--wf discharge`
- `--wf gw_daily`
- `--wf gw_periodic`

Example:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo create-new-project \
  --bbox -82.859 31.899 -82.013 32.947 \
  --wf discharge \
  --wf gw_daily \
  --output-dir dist/outputs/project_smoke
```

Expected shapefile outputs include:

- `discharge.shp`
- `daily.shp`
- `periodic.shp`

Each shapefile also writes:

- `.dbf`
- `.shx`
- `.prj`
- `.cpg`

The shapefile DBF uses NWIS-style field names from a code-local crosswalk rather than raw Water Data field names.

## Add Data

Use one workflow positional argument:

- `discharge`
- `gw_daily`
- `gw_periodic`

Example:

```bash
PYTHONPATH=src python -m waterdata_toolbox_demo add-data \
  discharge \
  --station-id 02225500 \
  --output-dir dist/outputs/data_smoke
```

The CSV body is reduced to:

- `Time`
- `Daily values`
- `Approval status`
- `Qualifier`

## Windows Build

Build the packaged Windows app on Windows:

```bash
pip install -e .[build]
pyinstaller waterdata_toolbox_demo.spec
```

The packaged executable is written to:

```text
dist/waterdata_toolbox_demo/waterdata_toolbox_demo.exe
```
