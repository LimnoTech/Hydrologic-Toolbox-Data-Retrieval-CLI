"""Station-discovery workflow logic for the sidecar package."""

from __future__ import annotations

import warnings

import pandas as pd


_INFER_FORMAT_WARNING_PATTERN = (
    r"Could not infer format, so each element will be parsed individually.*"
)


def _call_station_discovery_with_filtered_datetime_warning(function, **kwargs):
    """Call a waterdata discovery function while silencing the known date warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_INFER_FORMAT_WARNING_PATTERN,
            category=UserWarning,
        )
        return function(**kwargs)


def _extract_decimal_coordinate(value, axis):
    """Extract a latitude or longitude value from coordinate-like objects."""
    if value is None:
        return pd.NA

    coord = getattr(value, "y" if axis == "lat" else "x", None)
    if coord is not None:
        return coord

    if hasattr(value, "__geo_interface__"):
        coordinates = value.__geo_interface__.get("coordinates")
        if coordinates and len(coordinates) >= 2:
            return coordinates[1] if axis == "lat" else coordinates[0]

    return pd.NA


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
    """Convert a normalized station frame into an EPSG:4326 GeoDataFrame."""
    gpd = _load_geopandas()
    station_frame = frame.copy()

    station_frame["dec_long_va"] = pd.to_numeric(
        station_frame.get("dec_long_va"), errors="coerce"
    )
    station_frame["dec_lat_va"] = pd.to_numeric(
        station_frame.get("dec_lat_va"), errors="coerce"
    )

    existing_geometry = station_frame.get("geometry")
    if existing_geometry is not None and existing_geometry.notna().any():
        geometry = gpd.GeoSeries(existing_geometry, index=station_frame.index, crs="EPSG:4326")
        station_frame = station_frame.drop(columns=["geometry"])
    else:
        geometry_values = pd.Series([None] * len(station_frame), index=station_frame.index)
        valid_geometry = (
            station_frame["dec_long_va"].notna() & station_frame["dec_lat_va"].notna()
        )
        if valid_geometry.any():
            geometry_values.loc[valid_geometry] = list(
                gpd.points_from_xy(
                    station_frame.loc[valid_geometry, "dec_long_va"],
                    station_frame.loc[valid_geometry, "dec_lat_va"],
                )
            )
        geometry = gpd.GeoSeries(geometry_values, index=station_frame.index, crs="EPSG:4326")

    return gpd.GeoDataFrame(station_frame, geometry=geometry, crs="EPSG:4326")


def _normalize_station_frame(candidate_frame, qualifying_frame, workflow_type):
    """Reshape discovered stations into the legacy-style preview columns."""
    candidate_ids = set(candidate_frame["monitoring_location_id"])
    qualifying_ids = set(qualifying_frame["monitoring_location_id"])
    frame = candidate_frame[
        candidate_frame["monitoring_location_id"].isin(candidate_ids & qualifying_ids)
    ].copy()
    frame["workflow_type"] = workflow_type
    frame = frame.drop_duplicates(subset=["monitoring_location_id"])
    frame = frame.sort_values("monitoring_location_id").reset_index(drop=True)

    if frame.empty and "workflow_type" not in frame.columns:
        frame["workflow_type"] = pd.Series(dtype="object")

    if "site_no" not in frame.columns:
        if "monitoring_location_number" in frame.columns:
            frame["site_no"] = frame["monitoring_location_number"]
        elif "monitoring_location_id" in frame.columns:
            frame["site_no"] = frame["monitoring_location_id"].astype(str).str.replace(
                r"^USGS-", "", regex=True
            )
        else:
            frame["site_no"] = pd.Series(dtype="object")

    if "station_nm" not in frame.columns:
        if "monitoring_location_name" in frame.columns:
            frame["station_nm"] = frame["monitoring_location_name"]
        elif "location_name" in frame.columns:
            frame["station_nm"] = frame["location_name"]
        else:
            frame["station_nm"] = pd.Series(dtype="object")

    if "site_tp_cd" not in frame.columns:
        if "site_type_code" in frame.columns:
            frame["site_tp_cd"] = frame["site_type_code"]
        else:
            frame["site_tp_cd"] = pd.Series(dtype="object")

    if "dec_lat_va" not in frame.columns:
        if "latitude" in frame.columns:
            frame["dec_lat_va"] = frame["latitude"]
        elif "geometry" in frame.columns:
            frame["dec_lat_va"] = frame["geometry"].map(
                lambda value: _extract_decimal_coordinate(value, "lat")
            )
        else:
            frame["dec_lat_va"] = pd.Series([pd.NA] * len(frame), dtype="object")

    if "dec_long_va" not in frame.columns:
        if "longitude" in frame.columns:
            frame["dec_long_va"] = frame["longitude"]
        elif "geometry" in frame.columns:
            frame["dec_long_va"] = frame["geometry"].map(
                lambda value: _extract_decimal_coordinate(value, "lon")
            )
        else:
            frame["dec_long_va"] = pd.Series([pd.NA] * len(frame), dtype="object")

    if "state_cd" not in frame.columns:
        if "state_code" in frame.columns:
            frame["state_cd"] = frame["state_code"]
        else:
            frame["state_cd"] = pd.Series(dtype="object")

    if "county_cd" not in frame.columns:
        if "county_code" in frame.columns:
            frame["county_cd"] = frame["county_code"]
        else:
            frame["county_cd"] = pd.Series(dtype="object")

    return _to_station_geodataframe(frame)


def get_usgs_stations_in_bbox(bbox, workflow_types, waterdata_module=None):
    """Return workflow-keyed station discovery frames for the legacy new-project step."""
    if waterdata_module is None:
        from dataretrieval import waterdata as waterdata_module

    handlers = {
        "discharge": lambda: _normalize_station_frame(
            _call_station_discovery_with_filtered_datetime_warning(
                waterdata_module.get_monitoring_locations,
                bbox=bbox,
                site_type_code="ST",
            )[0],
            _call_station_discovery_with_filtered_datetime_warning(
                waterdata_module.get_time_series_metadata,
                bbox=bbox,
                parameter_code="00060",
            )[0],
            "discharge",
        ),
        "gw_daily": lambda: _normalize_station_frame(
            _call_station_discovery_with_filtered_datetime_warning(
                waterdata_module.get_monitoring_locations,
                bbox=bbox,
                site_type_code="GW",
            )[0],
            _call_station_discovery_with_filtered_datetime_warning(
                waterdata_module.get_time_series_metadata,
                bbox=bbox,
            )[0],
            "gw_daily",
        ),
        "gw_periodic": lambda: _normalize_station_frame(
            _call_station_discovery_with_filtered_datetime_warning(
                waterdata_module.get_monitoring_locations,
                bbox=bbox,
                site_type_code="GW",
            )[0],
            _call_station_discovery_with_filtered_datetime_warning(
                waterdata_module.get_field_measurements,
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
