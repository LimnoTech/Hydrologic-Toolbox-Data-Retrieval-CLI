"""Time-series workflow logic for the sidecar package."""

from __future__ import annotations

import warnings

from waterdata_toolbox_demo.exports import (
    export_timeseries_artifacts,
    format_artifact_messages,
)


_INFER_FORMAT_WARNING_PATTERN = (
    r"Could not infer format, so each element will be parsed individually.*"
)


def _normalize_monitoring_location_id(station_id):
    """Return the USGS-prefixed monitoring location id expected by waterdata calls."""
    return station_id if station_id.startswith("USGS-") else f"USGS-{station_id}"


def _call_waterdata_with_filtered_datetime_warning(function, **kwargs):
    """Call a waterdata retrieval function while silencing the known date warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_INFER_FORMAT_WARNING_PATTERN,
            category=UserWarning,
        )
        return function(**kwargs)


def get_usgs_timeseries(
    station_id,
    workflow_type,
    output_dir,
    parameter_code=None,
    date_range=("1880-01-01", "2100-01-01"),
    waterdata_module=None,
):
    """Return one legacy add-data payload plus exported artifacts for a station."""
    if waterdata_module is None:
        from dataretrieval import waterdata as waterdata_module

    monitoring_location_id = _normalize_monitoring_location_id(station_id)

    if workflow_type in {"discharge", "gw_daily"}:
        frame, metadata = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_daily,
            monitoring_location_id=monitoring_location_id,
            parameter_code="00060" if workflow_type == "discharge" else parameter_code,
            time=list(date_range),
        )
    elif workflow_type == "gw_periodic":
        frame, metadata = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_field_measurements,
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


def run_add_data_to_project_section(
    example_stations,
    output_dir,
    date_range,
    waterdata_module=None,
):
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
                waterdata_module=waterdata_module,
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
