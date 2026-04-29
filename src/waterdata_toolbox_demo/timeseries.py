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


def _select_matching_monitoring_location_row(monitoring_location_id, monitoring_locations_frame):
    """Prefer the monitoring-location row that matches the exported station id."""
    if (
        not isinstance(monitoring_locations_frame, pd.DataFrame)
        or monitoring_locations_frame.empty
    ):
        return None

    if "monitoring_location_id" in monitoring_locations_frame.columns:
        matches = monitoring_locations_frame.loc[
            monitoring_locations_frame["monitoring_location_id"] == monitoring_location_id
        ]
        if not matches.empty:
            return matches.iloc[0]

    return monitoring_locations_frame.iloc[0]


def _extract_decimal_coordinate(value, axis):
    """Extract a latitude or longitude value from a geometry-like object."""
    if value is None:
        return None

    coord = getattr(value, "y" if axis == "lat" else "x", None)
    if coord is not None:
        return coord

    if hasattr(value, "__geo_interface__"):
        coordinates = value.__geo_interface__.get("coordinates")
        if coordinates and len(coordinates) >= 2:
            return coordinates[1] if axis == "lat" else coordinates[0]

    return None


def _monitoring_location_coordinate(row, axis):
    """Return a latitude or longitude from raw monitoring-location values."""
    if row is None:
        return None

    raw_column_names = {
        "lat": ("latitude", "dec_lat_va"),
        "lon": ("longitude", "dec_long_va"),
    }
    for column_name in raw_column_names[axis]:
        value = _row_value(row, column_name)
        if value is not None:
            return value

    return _extract_decimal_coordinate(_row_value(row, "geometry"), axis)


def _monitoring_location_geometry(row):
    """Return one geometry value serialized as raw coordinates when possible."""
    geometry = _row_value(row, "geometry")
    if geometry is None:
        return None

    longitude = _extract_decimal_coordinate(geometry, "lon")
    latitude = _extract_decimal_coordinate(geometry, "lat")
    if longitude is not None and latitude is not None:
        return (longitude, latitude)

    return geometry


def _set_header_value(mapping, key, value):
    """Set one header value only when it is meaningfully present."""
    if value is None:
        return
    if isinstance(value, str) and value == "":
        return
    mapping[key] = value


def _build_csv_header_metadata(frame, metadata_frame, monitoring_locations_frame):
    """Build the raw API-derived metadata mapping for the reduced CSV export."""
    frame_row = frame.iloc[0] if isinstance(frame, pd.DataFrame) and not frame.empty else None
    metadata_row = _select_matching_timeseries_metadata_row(frame, metadata_frame)
    monitoring_location_id = _row_value(metadata_row, "monitoring_location_id") or _row_value(
        frame_row, "monitoring_location_id"
    )
    monitoring_location_row = _select_matching_monitoring_location_row(
        monitoring_location_id,
        monitoring_locations_frame,
    )
    return {
        "TS_ID": _row_value(frame_row, "time_series_id")
        or _row_value(metadata_row, "time_series_id"),
        "Parameter": _row_value(frame_row, "parameter_code")
        or _row_value(metadata_row, "parameter_code"),
        "Statistic": _row_value(frame_row, "statistic_id")
        or _row_value(metadata_row, "statistic_id"),
        "IV_TS_ID": _row_value(metadata_row, "parent_time_series_id"),
        "Description": _row_value(metadata_row, "parameter_description"),
        "site_no": monitoring_location_id,
        "Site number": _row_value(monitoring_location_row, "monitoring_location_number"),
        "Station name": _row_value(monitoring_location_row, "monitoring_location_name"),
        "Latitude": _monitoring_location_coordinate(monitoring_location_row, "lat"),
        "Longitude": _monitoring_location_coordinate(monitoring_location_row, "lon"),
        "HUC code": _row_value(monitoring_location_row, "hydrologic_unit_code"),
        "Drainage area": _row_value(monitoring_location_row, "drainage_area"),
    }


def _build_periodic_csv_header_metadata(monitoring_location_id, monitoring_locations_frame):
    """Build the modern Water Data metadata mapping for the periodic CSV export."""
    monitoring_location_row = _select_matching_monitoring_location_row(
        monitoring_location_id,
        monitoring_locations_frame,
    )
    header_metadata = {}

    _set_header_value(header_metadata, "monitoring_location_id", monitoring_location_id)
    _set_header_value(
        header_metadata,
        "monitoring_location_number",
        _row_value(monitoring_location_row, "monitoring_location_number"),
    )
    _set_header_value(
        header_metadata,
        "monitoring_location_name",
        _row_value(monitoring_location_row, "monitoring_location_name"),
    )
    _set_header_value(
        header_metadata,
        "site_type_code",
        _row_value(monitoring_location_row, "site_type_code"),
    )
    _set_header_value(
        header_metadata,
        "geometry",
        _monitoring_location_geometry(monitoring_location_row),
    )
    _set_header_value(
        header_metadata,
        "hydrologic_unit_code",
        _row_value(monitoring_location_row, "hydrologic_unit_code"),
    )
    _set_header_value(
        header_metadata,
        "altitude",
        _row_value(monitoring_location_row, "altitude"),
    )
    _set_header_value(
        header_metadata,
        "altitude_method_code",
        _row_value(monitoring_location_row, "altitude_method_code"),
    )
    _set_header_value(
        header_metadata,
        "altitude_accuracy",
        _row_value(monitoring_location_row, "altitude_accuracy"),
    )
    _set_header_value(
        header_metadata,
        "vertical_datum",
        _row_value(monitoring_location_row, "vertical_datum"),
    )
    _set_header_value(
        header_metadata,
        "district_code",
        _row_value(monitoring_location_row, "district_code"),
    )
    _set_header_value(
        header_metadata,
        "state_code",
        _row_value(monitoring_location_row, "state_code"),
    )
    _set_header_value(
        header_metadata,
        "county_code",
        _row_value(monitoring_location_row, "county_code"),
    )
    _set_header_value(
        header_metadata,
        "country_code",
        _row_value(monitoring_location_row, "country_code"),
    )
    _set_header_value(
        header_metadata,
        "time_zone_abbreviation",
        _row_value(monitoring_location_row, "time_zone_abbreviation"),
    )
    _set_header_value(
        header_metadata,
        "uses_daylight_savings",
        _row_value(monitoring_location_row, "uses_daylight_savings"),
    )
    _set_header_value(
        header_metadata,
        "construction_date",
        _row_value(monitoring_location_row, "construction_date"),
    )
    _set_header_value(
        header_metadata,
        "drainage_area",
        _row_value(monitoring_location_row, "drainage_area"),
    )
    _set_header_value(
        header_metadata,
        "contributing_drainage_area",
        _row_value(monitoring_location_row, "contributing_drainage_area"),
    )
    _set_header_value(
        header_metadata,
        "national_aquifer_code",
        _row_value(monitoring_location_row, "national_aquifer_code"),
    )
    _set_header_value(
        header_metadata,
        "aquifer_code",
        _row_value(monitoring_location_row, "aquifer_code"),
    )
    _set_header_value(
        header_metadata,
        "aquifer_type_code",
        _row_value(monitoring_location_row, "aquifer_type_code"),
    )
    _set_header_value(
        header_metadata,
        "well_constructed_depth",
        _row_value(monitoring_location_row, "well_constructed_depth"),
    )
    _set_header_value(
        header_metadata,
        "hole_constructed_depth",
        _row_value(monitoring_location_row, "hole_constructed_depth"),
    )
    _set_header_value(
        header_metadata,
        "depth_source_code",
        _row_value(monitoring_location_row, "depth_source_code"),
    )
    return header_metadata


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
    monitoring_locations_frame = None
    csv_header_metadata = None
    if workflow_type in {"discharge", "gw_daily"} and hasattr(
        waterdata_module, "get_time_series_metadata"
    ):
        timeseries_metadata_frame, _ = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_time_series_metadata,
            monitoring_location_id=monitoring_location_id,
            parameter_code=effective_parameter_code,
        )
    if workflow_type in {"discharge", "gw_daily", "gw_periodic"} and hasattr(
        waterdata_module, "get_monitoring_locations"
    ):
        monitoring_locations_frame, _ = _call_waterdata_with_filtered_datetime_warning(
            waterdata_module.get_monitoring_locations,
            monitoring_location_id=monitoring_location_id,
        )
    if workflow_type in {"discharge", "gw_daily"}:
        csv_header_metadata = _build_csv_header_metadata(
            frame,
            timeseries_metadata_frame,
            monitoring_locations_frame,
        )
    elif workflow_type == "gw_periodic":
        csv_header_metadata = _build_periodic_csv_header_metadata(
            monitoring_location_id,
            monitoring_locations_frame,
        )

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

