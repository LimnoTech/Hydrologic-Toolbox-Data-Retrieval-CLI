# Water Data ToolBox `.exe`

This repository packages a CLI-only Water Data ToolBox executable for Windows.

The packaged app supports two commands:

- `create-new-project`
- `add-data`

`create-new-project` writes one shapefile set per selected workflow. `add-data` writes the approved CSV output for one workflow at a time.

The packaged shapefile export uses a pure-Python writer, so the `.exe` does not rely on Fiona, pyogrio, or GDAL just to write the project shapefiles.

## Build The Windows App

Build the executable on Windows, not macOS.

From PowerShell in the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .[build]
pyinstaller waterdata_toolbox_demo.spec
```

The built app will be here:

```text
dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe
```

This is an `onedir` build, so keep the whole `dist\waterdata_toolbox_demo\` folder together.

## CLI Help

Run the executable with no arguments to print help:

```powershell
waterdata_toolbox_demo.exe
```

You can also call help explicitly:

```powershell
waterdata_toolbox_demo.exe --help
```

## Create New Project

Use one or more workflow flags:

- `--discharge`
- `--daily`
- `--periodic`

Example:

```powershell
waterdata_toolbox_demo.exe create-new-project --discharge --daily --output-dir dist\outputs\project_smoke
```

Optional bounding box input:

```powershell
waterdata_toolbox_demo.exe create-new-project --bbox -82.859 31.899 -82.013 32.947 --discharge --periodic --output-dir dist\outputs\project_bbox
```

Expected shapefile outputs include one set per selected workflow:

- `discharge.shp`
- `daily.shp`
- `periodic.shp`

Each shapefile also writes the normal sidecar files:

- `.shx`
- `.dbf`
- `.prj`
- `.cpg`

The shapefile DBF uses legacy NWIS field names from a code-local crosswalk. See (https://api.waterdata.usgs.gov/docs/ogcapi/migration/)

## Add Data

Use exactly one workflow flag:

- `--discharge`
- `--daily`
- `--periodic`

Discharge example:

```powershell
waterdata_toolbox_demo.exe add-data --discharge --station-id 02225500 --parameter-code 00060 --output-dir dist\outputs\data_smoke
```

Periodic groundwater example:

```powershell
waterdata_toolbox_demo.exe add-data --periodic --station-id 410947071344803 --parameter-code 72019 --start-date 1880-01-01 --end-date 2100-01-01 --output-dir dist\outputs\data_periodic
```

Expected discharge CSV output:

```text
dist\outputs\data_smoke\discharge_02225500.csv
```

## Output Summary

- `create-new-project` writes shapefiles
- `add-data` writes CSV
- the packaged executable does not launch the GUI
- the GUI code still exists in the repo for development/reference purposes

