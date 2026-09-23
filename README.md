# Hydrologic-Toolbox-DataRetrieval-CLI

This repository packages `Hydrologic-Toolbox-DataRetrieval-CLI`, a CLI-only
executable for Windows that retrieves USGS Water Data for the Hydrologic
Toolbox.

## About The Hydrologic Toolbox

The [Hydrologic Toolbox](https://doi.org/10.3133/tm4D3) is a USGS Windows
desktop application that analyzes hydrologic time-series data through a
graphical and mapping interface. It consolidates the earlier USGS Groundwater
Toolbox (2014) and Surface-Water Toolbox (2018), and provides standard methods
for hydrograph separation — BFI, HYSEP, PART, SWAT Bflow, and Eckhardt's
two-parameter digital filter — along with RORA and RECESS for estimating
groundwater recharge from streamflow records.

Those analyses run on streamflow and groundwater-level data from the USGS
National Water Information System. This repository supplies that retrieval
step: the Toolbox calls `Hydrologic-Toolbox-DataRetrieval-CLI` with an XML
request, the CLI queries the USGS Water Data APIs, and station shapefiles or
time-series CSVs are written to a target folder. See
[HydrologicToolbox XML](#hydrologictoolbox-xml) for the request format.

Published as USGS Techniques and Methods, book 4, chapter D3 (Barlow and
others, 2022).

## Websites

| Resource | Link |
| --- | --- |
| Hydrologic Toolbox (USGS Techniques and Methods 4-D3) | <https://doi.org/10.3133/tm4D3> |
| USGS Water Data APIs overview | <https://www.usgs.gov/tools/usgs-water-data-apis> |
| USGS Water Data API hub | <https://api.waterdata.usgs.gov/> |

## Run The CLI

Build the Windows app, then open PowerShell and either:

```powershell
cd .\dist\hydrologic_toolbox_data_retrieval_cli
.\hydrologic_toolbox_data_retrieval_cli.exe --help
```

or run it from the repo root:

```powershell
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe --help
```

## HydrologicToolbox XML

The direct CLI remains available for manual use. HydrologicToolbox integration
uses the XML entrypoint instead:

`xml-compat` prints exactly one XML response string:
- `<success>...</success>` when files were written
- `<error>...</error>` when required XML tags are missing or invalid

Add `--debug` to write progress messages to `stderr`, or add `--debug-log` to
append those messages to a file. The XML response stays on `stdout`. This is
useful when checking whether the executable read the XML, parsed it, started a
Water Data request, and wrote the output file.

If it is easier for a calling app, set `WATERDATA_TOOLBOX_DEBUG=1` or
`WATERDATA_TOOLBOX_DEBUG_LOG=C:\temp\waterdata_toolbox_debug.log` instead of
passing debug flags.

```cmd
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe xml-compat --xml "<function name='GetNWISDailyDischarge'><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>"
```

```cmd
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe xml-compat --debug --xml "<function name='GetNWISDailyDischarge'><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>"
```

```cmd
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe xml-compat --debug-log C:\temp\waterdata_toolbox_debug.log --xml "<function name='GetNWISDailyDischarge'><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>"
```

PowerShell can be pickier about passing raw inline XML to a native `.exe`. If
you need to run it from PowerShell, use `--%`:

```powershell
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe --% xml-compat --xml "<function name='GetNWISDailyDischarge'><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>"
```

```powershell
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe --% xml-compat --debug --xml "<function name='GetNWISDailyDischarge'><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>"
```

```powershell
.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe --% xml-compat --debug-log C:\temp\waterdata_toolbox_debug.log --xml "<function name='GetNWISDailyDischarge'><arguments><SaveIn>C:\temp\out</SaveIn><stationid>02336106</stationid></arguments></function>"
```

The XML request is treated as a superset envelope. Extra tags that are not
needed for the Water Data request are ignored.

`xml-compat` can receive either one `<function>...</function>` document or a
bundle containing multiple top-level `<function>` blocks. When a bundle is
received, supported valid Water Data functions are processed in order and the
results are returned in one `<success>` response.

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
| `.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe create-new-project --wf discharge --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_discharge` | Writes the `discharge` shapefile set to the output folder. |
| `.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe create-new-project --wf discharge --wf gw_daily --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_multi` | Writes one shapefile set for each selected workflow. |
| `.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe create-new-project --wf gw_periodic --bbox -82.859 31.899 -82.013 32.947 --output-dir dist\outputs\create_new_project_periodic_bbox` | Limits station discovery to the supplied bounding box and writes the `periodic` shapefile set. |
| `.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe add-data discharge --station-id 02225500 --output-dir dist\outputs\add_data_discharge` | Writes `discharge_02225500.csv` with the approved header and body format. |
| `.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe add-data gw_daily --station-id 324209082430201 --output-dir dist\outputs\add_data_daily` | Writes `gw_daily_324209082430201.csv` with the approved header and body format. |
| `.\dist\hydrologic_toolbox_data_retrieval_cli\hydrologic_toolbox_data_retrieval_cli.exe add-data gw_periodic --station-id 410947071344803 --start-date 1880-01-01 --end-date 2100-01-01 --output-dir dist\outputs\add_data_periodic` | Writes `gw_periodic_410947071344803.csv` with a commented metadata header and a periodic measurement table. |

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
