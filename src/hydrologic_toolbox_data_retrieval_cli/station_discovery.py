"""CSV-only station-discovery workflow logic for the packaged app."""

from __future__ import annotations

import warnings

import pandas as pd

from hydrologic_toolbox_data_retrieval_cli.exports import (
    export_station_shapefile_artifacts,
    format_artifact_messages,
)
from hydrologic_toolbox_data_retrieval_cli.frame_types import categorize_existing_columns


_INFER_FORMAT_WARNING_PATTERN = (
    r"Could not infer format, so each element will be parsed individually.*"
)

_STATION_CATEGORICAL_COLUMNS = [
    "agency_code",
    "monitoring_location_id",
    "monitoring_location_number",
    "monitoring_location_name",
    "site_type_code",
    "horizontal_position_method_code",
    "original_horizontal_datum",
    "district_code",
    "state_code",
    "county_code",
    "country_code",
    "hydrologic_unit_code",
    "basin_code",
    "time_zone_abbreviation",
    "national_aquifer_code",
    "aquifer_code",
    "aquifer_type_code",
    "depth_source_code",
]


def _call_station_discovery_with_filtered_datetime_warning(function, **kwargs):
    """Call a waterdata discovery function while silencing the known date warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_INFER_FORMAT_WARNING_PATTERN,
            category=UserWarning,
        )
        return function(**kwargs)


def _load_geopandas():
    """Import GeoPandas only when the discovery workflow needs it."""
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "Install `geopandas` to use GeoDataFrame station discovery support."
        ) from exc
    return gpd


def _to_station_geodataframe(frame):
    """Convert a filtered raw station frame into an EPSG:4326 GeoDataFrame."""
    gpd = _load_geopandas()
    station_frame = frame.copy()

    existing_geometry = station_frame.get("geometry")
    if existing_geometry is not None and existing_geometry.notna().any():
        geometry = gpd.GeoSeries(existing_geometry, index=station_frame.index, crs="EPSG:4326")
        station_frame = station_frame.drop(columns=["geometry"])
    else:
        longitude_column = None
        latitude_column = None
        if "longitude" in station_frame.columns and "latitude" in station_frame.columns:
            longitude_column = "longitude"
            latitude_column = "latitude"
        elif "dec_long_va" in station_frame.columns and "dec_lat_va" in station_frame.columns:
            longitude_column = "dec_long_va"
            latitude_column = "dec_lat_va"

        geometry_values = pd.Series([None] * len(station_frame), index=station_frame.index)
        if longitude_column is None or latitude_column is None:
            valid_geometry = pd.Series([False] * len(station_frame), index=station_frame.index)
            longitude_values = pd.Series([pd.NA] * len(station_frame), index=station_frame.index)
            latitude_values = pd.Series([pd.NA] * len(station_frame), index=station_frame.index)
        else:
            longitude_values = pd.to_numeric(
                station_frame[longitude_column],
                errors="coerce",
            )
            latitude_values = pd.to_numeric(
                station_frame[latitude_column],
                errors="coerce",
            )
            valid_geometry = longitude_values.notna() & latitude_values.notna()

        if valid_geometry.any():
            geometry_values.loc[valid_geometry] = list(
                gpd.points_from_xy(
                    longitude_values.loc[valid_geometry],
                    latitude_values.loc[valid_geometry],
                )
            )
        geometry = gpd.GeoSeries(geometry_values, index=station_frame.index, crs="EPSG:4326")

    return gpd.GeoDataFrame(station_frame, geometry=geometry, crs="EPSG:4326")


def _normalize_station_frame(candidate_frame, qualifying_frame, workflow_type):
    """Filter discovered stations while preserving the raw monitoring-location schema."""
    candidate_ids = set(candidate_frame["monitoring_location_id"])
    qualifying_ids = set(qualifying_frame["monitoring_location_id"])
    frame = candidate_frame[
        candidate_frame["monitoring_location_id"].isin(candidate_ids & qualifying_ids)
    ].copy()
    frame = frame.drop_duplicates(subset=["monitoring_location_id"])
    frame = frame.sort_values("monitoring_location_id").reset_index(drop=True)
    frame = categorize_existing_columns(frame, _STATION_CATEGORICAL_COLUMNS)

    return _to_station_geodataframe(frame)


def _get_station_discovery_frames(bbox, workflow_type, waterdata_module):
    """Return candidate, qualifying, and normalized frames for one workflow."""
    if workflow_type == "discharge":
        candidate_frame = _call_station_discovery_with_filtered_datetime_warning(
            waterdata_module.get_monitoring_locations,
            bbox=bbox,
            site_type_code="ST",
        )[0]
        qualifying_frame = _call_station_discovery_with_filtered_datetime_warning(
            waterdata_module.get_time_series_metadata,
            bbox=bbox,
            parameter_code="00060",
        )[0]
    elif workflow_type == "gw_daily":
        candidate_frame = _call_station_discovery_with_filtered_datetime_warning(
            waterdata_module.get_monitoring_locations,
            bbox=bbox,
            site_type_code="GW",
        )[0]
        qualifying_frame = _call_station_discovery_with_filtered_datetime_warning(
            waterdata_module.get_time_series_metadata,
            bbox=bbox,
        )[0]
    elif workflow_type == "gw_periodic":
        candidate_frame = _call_station_discovery_with_filtered_datetime_warning(
            waterdata_module.get_monitoring_locations,
            bbox=bbox,
            site_type_code="GW",
        )[0]
        qualifying_frame = _call_station_discovery_with_filtered_datetime_warning(
            waterdata_module.get_field_measurements,
            bbox=bbox,
        )[0]
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")

    normalized_frame = _normalize_station_frame(
        candidate_frame,
        qualifying_frame,
        workflow_type,
    )
    return candidate_frame, qualifying_frame, normalized_frame


def run_create_new_project_section(
    bbox,
    workflow_types,
    output_dir,
    waterdata_module=None,
    output_projection=None,
):
    """Run create-project discovery and write one shapefile per workflow."""
    if waterdata_module is None:
        from dataretrieval import waterdata as waterdata_module

    workflow_payloads = {}
    output_stems = {
        "discharge": "discharge",
        "gw_daily": "daily",
        "gw_periodic": "periodic",
    }
    for workflow_type in workflow_types:
        _, _, frame = _get_station_discovery_frames(
            bbox,
            workflow_type,
            waterdata_module,
        )
        file_paths = export_station_shapefile_artifacts(
            frame,
            output_dir,
            output_stems[workflow_type],
            output_projection=output_projection,
        )
        workflow_payloads[workflow_type] = {
            "frame": frame,
            "files": file_paths,
            "artifact_messages": format_artifact_messages(file_paths),
        }
    return workflow_payloads
