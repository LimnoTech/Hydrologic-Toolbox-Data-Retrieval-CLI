"""CSV-only time-series workflow logic for the packaged app."""

from __future__ import annotations

import warnings

import pandas as pd

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


def _row_value(row, column_name):
    """Return a pandas row value or None when the field is missing."""
    if row is None:
        return None

    value = row.get(column_name)
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def _select_matching_timeseries_metadata_row(frame, metadata_frame):
    """Prefer the metadata row that matches the exported daily-series id."""
    if not isinstance(metadata_frame, pd.DataFrame) or metadata_frame.empty:
        return None

    if isinstance(frame, pd.DataFrame) and not frame.empty and "time_series_id" in frame.columns:
        daily_time_series_id = frame.iloc[0].get("time_series_id")
        matches = metadata_frame.loc[metadata_frame["time_series_id"] == daily_time_series_id]
        if not matches.empty:
            return matches.iloc[0]

    return metadata_frame.iloc[0]


def _build_csv_header_metadata(frame, metadata_frame):
    """Build the raw API-derived metadata mapping for the reduced CSV export."""
    frame_row = frame.iloc[0] if isinstance(frame, pd.DataFrame) and not frame.empty else None
    metadata_row = _select_matching_timeseries_metadata_row(frame, metadata_frame)
    return {
        "TS_ID": _row_value(frame_row, "time_series_id") or _row_value(metadata_row, "time_series_id"),
        "Parameter": _row_value(frame_row, "parameter_code")
        or _row_value(metadata_row, "parameter_code"),
        "Statistic": _row_value(frame_row, "statistic_id")
        or _row_value(metadata_row, "statistic_id"),
        "IV_TS_ID": _row_value(metadata_row, "parent_time_series_id"),
        "Description": _row_value(metadata_row, "parameter_description"),
        "site_no": _row_value(metadata_row, "monitoring_location_id")
        or _row_value(frame_row, "monitoring_location_id"),
    }


def get_usgs_timeseries(
    station_id,
    workflow_type,
    output_dir,
    parameter_code=None,
    date_range=("1880-01-01", "2100-01-01"),
    waterdata_module=None,
):
    """Return one add-data payload plus the exported CSV artifact for a station."""
    if waterdata_module is None:
        from dataretrieval import waterdata as waterdata_module

    monitoring_location_id = _normalize_monitoring_location_id(station_id)
    effective_parameter_code = "00060" if workflow_type == "discharge" else parameter_code

    if workflow_type in {"discharge", "gw_daily"}:
        frame, metadata = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_daily,
            monitoring_location_id=monitoring_location_id,
            parameter_code=effective_parameter_code,
            time=list(date_range),
        )
    elif workflow_type == "gw_periodic":
        frame, metadata = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_field_measurements,
            monitoring_location_id=monitoring_location_id,
            parameter_code=effective_parameter_code,
            time=list(date_range),
        )
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")

    metadata_dict = metadata if isinstance(metadata, dict) else vars(metadata).copy()
    timeseries_metadata_frame = None
    csv_header_metadata = None
    if workflow_type in {"discharge", "gw_daily"} and hasattr(
        waterdata_module, "get_time_series_metadata"
    ):
        timeseries_metadata_frame, _ = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_time_series_metadata,
            monitoring_location_id=monitoring_location_id,
            parameter_code=effective_parameter_code,
        )
        csv_header_metadata = _build_csv_header_metadata(frame, timeseries_metadata_frame)

    frame = frame.reset_index(drop=True).copy()
    frame["station_id"] = station_id
    frame["workflow_type"] = workflow_type

    records = frame.to_dict(orient="records")
    file_paths = export_timeseries_artifacts(
        frame,
        output_dir,
        workflow_type,
        station_id,
        csv_header_metadata=csv_header_metadata,
    )
    if frame.empty:
        metadata_dict = {
            **metadata_dict,
            "warning": f"No records returned for {workflow_type} {station_id}",
        }
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
