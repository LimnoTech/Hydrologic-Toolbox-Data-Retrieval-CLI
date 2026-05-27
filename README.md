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

## HydrologicToolbox XML

The direct CLI remains available for manual use. HydrologicToolbox integration
uses the XML entrypoint instead:

```powershell
.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe xml-compat --xml '<function name="GetNWISDailyDischarge"><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>'
```

`xml-compat` prints exactly one XML response string:
- `<success>...</success>` when files were written
- `<error>...</error>` when required XML tags are missing or invalid

The XML request is treated as a superset envelope. Extra tags that are not
needed for the Water Data request are ignored.

Supported XML request shapes:

- Station discovery:
  - function name: `GetNWISStations`
  - required tags: `SaveIn`, one or more `DataType`, and `<region>` with `northbc`, `southbc`, `eastbc`, `westbc`, and `projection`
  - supported `DataType` values: `discharge`, `gw_daily`, `gw_periodic`
  - optional tag: `DesiredProjection`
- Add-data:
  - function names are mapped by name to the Water Data workflow, for example:
    - `GetNWISDailyDischarge` -> `discharge`
    - `GetNWISDailyGroundwater` -> `gw_daily`
    - `GetNWISPeriodicGroundwater` -> `gw_periodic`
  - required tags: `SaveIn` and one or more `stationid`
  - one output file is written per station

Defaults and behavior:

- If `DesiredProjection` is missing, station shapefiles are written in WGS84 / `EPSG:4326`
- Projected `<region>` bounds are transformed to WGS84 before the Water Data API call
- Failures return `<error>...</error>` instead of raw tracebacks

Example station request:

```xml
<function name="GetNWISStations">
  <arguments>
    <DataType>discharge</DataType>
    <DataType>gw_daily</DataType>
    <SaveIn>C:\temp\out</SaveIn>
    <DesiredProjection>+proj=aea +ellps=GRS80 +lon_0=-96 +lat_0=23.0 +lat_1=29.5 +lat_2=45.5 +x_0=0 +y_0=0 +datum=NAD83 +units=m</DesiredProjection>
    <region>
      <northbc>4116087.71455496</northbc>
      <southbc>3971380.60224013</southbc>
      <eastbc>-9284994.6510355</eastbc>
      <westbc>-9412819.34952669</westbc>
      <projection>+x_0=0 +y_0=0 +lon_0=0 +lat_1=0 +proj=merc +ellps=WGS84 +no_defs</projection>
    </region>
  </arguments>
</function>
```

Example success responses:

```xml
<success><add_shape workflow="discharge">C:\temp\out\discharge.shp</add_shape><add_shape workflow="gw_daily">C:\temp\out\gw_daily.shp</add_shape></success>
```

```xml
<success><add_data type="CSV" subtype="discharge" stationid="02336106">C:\temp\out\discharge_02336106.csv</add_data></success>
```

## Commands

These examples assume you are running from the repo root in PowerShell.

| Command | Result |
| --- | --- |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe create-new-project --wf discharge --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_discharge` | Writes the `discharge` shapefile set to the output folder. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe create-new-project --wf discharge --wf gw_daily --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_multi` | Writes one shapefile set for each selected workflow. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe create-new-project --wf gw_periodic --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_periodic_bbox` | Limits station discovery to the supplied bounding box and writes the `periodic` shapefile set. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data discharge --station-id 02225500 --output-dir dist\outputs\add_data_discharge` | Writes `discharge_02225500.csv` with the approved header and body format. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data gw_daily --station-id 324209082430201 --output-dir dist\outputs\add_data_daily` | Writes `gw_daily_324209082430201.csv` with the approved header and body format. |
| `.\dist\waterdata_toolbox_demo\waterdata_toolbox_demo.exe add-data gw_periodic --station-id 410947071344803 --start-date 1880-01-01 --end-date 2100-01-01 --output-dir dist\outputs\add_data_periodic` | Writes `gw_periodic_410947071344803.csv` with a commented metadata header and a periodic measurement table. |

For `add-data`, the workflow name chooses the built-in USGS parameter automatically:
- `discharge` -> `00060`
- `gw_daily` -> `72019`
- `gw_periodic` -> `72019`

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
