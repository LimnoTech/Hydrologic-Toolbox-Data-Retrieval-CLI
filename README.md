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
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data discharge --station-id 02225500 --output-dir dist\outputs\add_data_discharge` | Writes `discharge_02225500.csv` with the approved header and body format. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data daily --station-id 324209082430201 --output-dir dist\outputs\add_data_daily` | Writes `gw_daily_324209082430201.csv` with the approved header and body format. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data periodic --station-id 410947071344803 --start-date 1880-01-01 --end-date 2100-01-01 --output-dir dist\outputs\add_data_periodic` | Writes `gw_periodic_410947071344803.csv` for the requested station and date range. |

For `add-data`, the workflow shorthand chooses the built-in USGS parameter automatically:
- `discharge` -> `00060`
- `daily` -> `72019`
- `periodic` -> `72019`

## Crosswalk Note

For shapefile attribute tables, the CLI maps raw Water Data field names to NWIS-style names first, then writes shapefile-safe field names from that mapping. The USGS migration guide is the reference for those aliases: [USGS Water Data migration guide](https://api.waterdata.usgs.gov/docs/ogcapi/migration/).

| Water Data field | NWIS-style name | Shapefile field |
| --- | --- | --- |
| `agency_code` | `agency_cd` | `agency_cd` |
| `monitoring_location_number` | `site_no` | `site_no` |
| `monitoring_location_name` | `station_nm` | `station_nm` |
| `site_type_code` | `site_tp_cd` | `site_tp_cd` |
| `hydrologic_unit_code` | `huc_cd` | `huc_cd` |
| `drainage_area` | `drain_area_va` | `drain_area` |
| `geometry` | `dec_lat_va` / `dec_long_va` | `dec_lat_va` / `dec_long_v` |
