# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: default
#     language: python
#     name: python3
# ---

# %% [markdown]
# # USGS Water Data Demo
#

# %% [markdown]
# This notebook demonstrates how to use the new USGS water data retrieval Python API, [`dataretrieval`](https://doi-usgs.github.io/dataretrieval-python/), to grab the station information needed for the [USGS Hydrologic Toolbox](https://pubs.usgs.gov/tm/04/d03/tm4d3.pdf).
#
#
# ## Useful Links
#
# - [`dataretrieval` documentation](https://doi-usgs.github.io/dataretrieval-python/)
# - [`dataretrieval` GitHub repository](https://github.com/DOI-USGS/dataretrieval-python)
# - [Introduction to the `waterdata` module example notebook](https://doi-usgs.github.io/dataretrieval-python/examples/index.html)
# - [USGS Water Data APIs documentation](https://api.waterdata.usgs.gov/docs/)
# - [USGS Monitoring Locations endpoint](https://api.waterdata.usgs.gov/ogcapi/v0/collections/monitoring-locations?f=html)
# - [USGS migration guide for modernized Water Data APIs](https://api.waterdata.usgs.gov/docs/ogcapi/migration/)
#

# %%
import sys
from pathlib import Path

import pandas as pd
from IPython.display import display
from dataretrieval import waterdata as wd
for candidate in (Path.cwd().resolve(), Path.cwd().resolve().parent):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)
from dataretrieval import waterdata as wd
import helpers
from helpers.usgs_waterdata_demo import (
    DEMO_CONFIG,
    NOTEBOOK_MAPPING_ROWS,
    _call_station_discovery_with_filtered_datetime_warning,
    _call_waterdata_with_filtered_datetime_warning,
    _normalize_monitoring_location_id,
    _normalize_station_frame,
    export_timeseries_artifacts,
    format_artifact_messages,
    render_plot_selector,
    render_station_discovery_selector,
)

# %%
PROJECT_ROOT = Path(helpers.__file__).resolve().parent.parent

# %% [markdown]
# ## Sample Data
#
# Demo_Config is dummy data generated to display the type of scenarios we see in the hydrological toolbox.
# 1. New Project: Bounding Box 
# 2. Add data: Time series, Parameter code(measurement variable for example ground water 72019), Station
#     

# %%
DEMO_CONFIG


# %% [markdown]
# ## Legacy .Net to Modern Water Data Reterival Mapping
# Demonstrates old purpose and new purpose mainly used this for my own understanding. 

# %%
pd.DataFrame(NOTEBOOK_MAPPING_ROWS)


# %% [markdown]
# ## Creating New Project
#
# This section mirrors the legacy bounding-box station discovery calls for `discharge`, `gw_daily`, and `gw_periodic`.
#
# The discovered station results are GeoPandas `GeoDataFrame`s, so they carry both tabular station attributes and GIS-style geometry in memory. We are not writing shapefiles here, Use`gdf.crs` to confirm the spatial metadata is present :).

# %% [markdown]
# This section keeps the real `dataretrieval.waterdata` station-discovery calls in the notebook so shows exactly how to use them while matching the old bbox-search theme.
#
# - Old discharge site search theme: `siteType=ST`, `hasDataTypeCd=dv`, `parameterCd=00060`.
# - Old gw_daily site search theme: `siteType=GW`, `hasDataTypeCd=dv`.
# - Old gw_periodic site search theme: broader bbox station discovery without the daily-value filter.
# - `wd.get_monitoring_locations(bbox=bbox, site_type_code="ST" or "GW")` returns monitoring sites inside the bounding box.
# - `wd.get_time_series_metadata(bbox=bbox, parameter_code="00060")` narrows those sites to locations with daily time-series metadata.
# - `wd.get_field_measurements(bbox=bbox)` finds groundwater stations that have periodic field measurements.
# - Use `bbox=(west, south, east, north)` in decimal degrees to mirror the old XML bounding-box inputs.
#

# %%
def get_usgs_stations_in_bbox(bbox, workflow_types):
    """Return workflow-keyed station discovery frames for the legacy new-project step.

    This demo mirrors the old bbox site searches with `waterdata` calls:
    `get_monitoring_locations` finds candidate stations, then
    `get_time_series_metadata` or `get_field_measurements` filters those
    candidates down to the workflow-specific stations we want to preview.
    """
    handlers = {
        "discharge": lambda: _normalize_station_frame(
            _call_station_discovery_with_filtered_datetime_warning(
                wd.get_monitoring_locations,
                bbox=bbox,
                site_type_code="ST",
            )[0],
            _call_station_discovery_with_filtered_datetime_warning(
                wd.get_time_series_metadata,
                bbox=bbox,
                parameter_code="00060",
            )[0],
            "discharge",
        ),
        "gw_daily": lambda: _normalize_station_frame(
            _call_station_discovery_with_filtered_datetime_warning(
                wd.get_monitoring_locations,
                bbox=bbox,
                site_type_code="GW",
            )[0],
            _call_station_discovery_with_filtered_datetime_warning(
                wd.get_time_series_metadata,
                bbox=bbox,
            )[0],
            "gw_daily",
        ),
        "gw_periodic": lambda: _normalize_station_frame(
            _call_station_discovery_with_filtered_datetime_warning(
                wd.get_monitoring_locations,
                bbox=bbox,
                site_type_code="GW",
            )[0],
            _call_station_discovery_with_filtered_datetime_warning(
                wd.get_field_measurements,
                bbox=bbox,
            )[0],
            "gw_periodic",
        ),
    }

    results = {}
    for workflow_type in workflow_types:
        if workflow_type not in handlers:
            raise ValueError(f"Unsupported workflow type: {workflow_type}")
        results[workflow_type] = handlers[workflow_type]()
    return results



# %%
create_section_results = get_usgs_stations_in_bbox(
    DEMO_CONFIG["bbox"],
    ["discharge", "gw_daily", "gw_periodic"],
)

create_preview_columns = [
    "site_no",
    "station_nm",
    "site_tp_cd",
    "dec_lat_va",
    "dec_long_va",
    "state_cd",
    "county_cd",
]

for workflow_type, frame in create_section_results.items():
    print(f"{workflow_type}: {len(frame)} stations")
    print(f"frame type: {type(frame).__name__}")
    print(f"crs: {frame.crs}")
    available_columns = [column for column in create_preview_columns if column in frame.columns]
    preview_columns = available_columns + ["geometry"] if "geometry" in frame.columns else available_columns
    display(frame[preview_columns].head() if preview_columns else frame.head())

# %%
discharge_df = create_section_results['discharge']
discharge_df.info()

# %%
render_station_discovery_selector(create_section_results)


# %% [markdown]
# ## Adding Data to Project
#

# %% [markdown]
# This section mimics the same structure of the xml file. Here is a over view. 
# - Old discharge add-data theme: daily-values style station pull with `parameterCd=00060`.
# - Old gw_daily add-data theme: daily-values style groundwater station pull.
# - Old gw_periodic add-data theme: groundwater-level / field-measurement station retrieval rather than a bbox search.
# - `wd.get_daily(monitoring_location_id="USGS-...", parameter_code="00060" or another code, time=[start, end])` returns daily values.
# - `wd.get_field_measurements(monitoring_location_id="USGS-...", parameter_code="72019", time=[start, end])` returns periodic groundwater field measurements.
# - `monitoring_location_id` should use the `USGS-...` prefix expected by `waterdata`.
# - `parameter_code` and `time` mirror the old XML inputs for station, variable, and period of record.
#

# %%
def get_usgs_timeseries(
    station_id,
    workflow_type,
    output_dir,
    parameter_code=None,
    date_range=("1880-01-01", "2100-01-01"),
):
    """Return one legacy add-data payload plus exported artifacts for a station.

    `discharge` and `gw_daily` use `wd.get_daily`, while `gw_periodic`
    uses `wd.get_field_measurements` to match the old groundwater-level
    retrieval theme without recreating the raw RDB files.
    """
    monitoring_location_id = _normalize_monitoring_location_id(station_id)

    if workflow_type in {"discharge", "gw_daily"}:
        frame, metadata = _call_waterdata_with_filtered_datetime_warning(
            wd.get_daily,
            monitoring_location_id=monitoring_location_id,
            parameter_code="00060" if workflow_type == "discharge" else parameter_code,
            time=list(date_range),
        )
    elif workflow_type == "gw_periodic":
        frame, metadata = _call_waterdata_with_filtered_datetime_warning(
            wd.get_field_measurements,
            monitoring_location_id=monitoring_location_id,
            parameter_code=parameter_code,
            time=list(date_range),
        )
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")

    metadata_dict = metadata if isinstance(metadata, dict) else vars(metadata).copy()

    frame = frame.reset_index(drop=True).copy()
    frame["station_id"] = station_id
    frame["workflow_type"] = workflow_type

    if frame.empty:
        return {
            "frame": frame,
            "records": [],
            "files": {},
            "metadata": {
                **metadata_dict,
                "warning": f"No records returned for {workflow_type} {station_id}",
            },
        }

    records = frame.to_dict(orient="records")
    file_paths = export_timeseries_artifacts(frame, output_dir, workflow_type, station_id)
    return {
        "frame": frame,
        "records": records,
        "files": file_paths,
        "metadata": metadata_dict,
    }



# %%
def run_add_data_to_project_section(example_stations, output_dir, date_range):
    """Run the legacy add-data demo section for each configured workflow type."""
    results = {}
    for workflow_type, example in example_stations.items():
        try:
            payload = get_usgs_timeseries(
                example["station_id"],
                workflow_type,
                output_dir,
                parameter_code=example.get("parameter_code"),
                date_range=date_range,
            )
        except Exception as exc:
            results[workflow_type] = {
                "payload": None,
                "error": str(exc),
                "artifact_messages": [],
            }
            continue

        results[workflow_type] = {
            "payload": payload,
            "error": None,
            "artifact_messages": format_artifact_messages(payload["files"]),
        }
    return results



# %%
add_data_results = run_add_data_to_project_section(
    DEMO_CONFIG["example_stations"],
    PROJECT_ROOT / DEMO_CONFIG["output_dir"],
    DEMO_CONFIG["date_range"],
)

for workflow_type, result in add_data_results.items():
    print(workflow_type)
    if result["error"]:
        print(f"Warning: {result['error']}")
        continue

    payload = result["payload"]
    display(payload["frame"].head())
    for message in result["artifact_messages"]:
        print(message)

# %% [markdown]
# ## Plot Generated Outputs
#

# %% [markdown]
# This section plots the generated station-based outputs created above, keeping the add-data widget focused on the daily-values versus groundwater-level retrieval differences.
#
# Plot frame preparation lives in helpers.usgs_waterdata_demo._prepare_plot_frame.
# Plot rendering lives in helpers.usgs_waterdata_demo.plot_generated_output.
# Widget rendering lives in helpers.usgs_waterdata_demo.render_plot_selector.

# %%
render_plot_selector(add_data_results)


# %%

# %%

# %% [markdown]
# # END
