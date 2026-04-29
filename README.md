# Water Data ToolBox `.exe`

This repository packages a CLI-only Water Data ToolBox executable for Windows.

## Run The CLI

Build the Windows app, then open PowerShell and either:

```powershell
cd .\dist\waterdata_toolbox_demo
.\waterdata_toolbox_demo.exe --help
```

or run it from the repo root:

```powershell
.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe --help
```

## Commands

These examples assume you are running from the repo root in PowerShell.

| Command | Result |
| --- | --- |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe create-new-project --wf discharge --output-dir dist\outputs\create_new_project_discharge` | Writes the `discharge` shapefile set to the output folder. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe create-new-project --wf discharge --wf daily --output-dir dist\outputs\create_new_project_multi` | Writes one shapefile set for each selected workflow. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe create-new-project --wf periodic --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_periodic_bbox` | Limits station discovery to the supplied bounding box and writes the `periodic` shapefile set. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data discharge --station-id 02225500 --parameter-code 00060 --output-dir dist\outputs\add_data_discharge` | Writes `discharge_02225500.csv` with the approved header and body format. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data daily --station-id 324209082430201 --parameter-code 72019 --output-dir dist\outputs\add_data_daily` | Writes `gw_daily_324209082430201.csv` with the approved header and body format. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data periodic --station-id 410947071344803 --parameter-code 72019 --start-date 1880-01-01 --end-date 2100-01-01 --output-dir dist\outputs\add_data_periodic` | Writes `gw_periodic_410947071344803.csv` for the requested station and date range. |
