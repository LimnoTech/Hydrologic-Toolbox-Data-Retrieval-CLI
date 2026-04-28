# Water Data ToolBox `.exe`

This repository packages a CLI-only Water Data Hydro ToolBox executable for Windows.

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

| Command | Result |
| --- | --- |
| `.\waterdata_toolbox_demo.exe create-new-project --wf discharge --output-dir dist\outputs\project_smoke` | Writes the `discharge` shapefile set to the output folder. |
| `.\waterdata_toolbox_demo.exe create-new-project --wf discharge --wf daily --output-dir dist\outputs\project_smoke` | Writes one shapefile set for each selected workflow. |
| `.\waterdata_toolbox_demo.exe create-new-project --wf periodic --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\project_bbox` | Limits station discovery to the supplied bounding box and writes the `periodic` shapefile set. |
| `.\waterdata_toolbox_demo.exe add-data discharge --station-id 02225500 --parameter-code 00060 --output-dir dist\outputs\data_smoke` | Writes `discharge_02225500.csv` with the approved header and body format. |
| `.\waterdata_toolbox_demo.exe add-data periodic --station-id 410947071344803 --parameter-code 72019 --start-date 1880-01-01 --end-date 2100-01-01 --output-dir dist\outputs\data_periodic` | Writes one periodic groundwater CSV for the requested station and date range. |
