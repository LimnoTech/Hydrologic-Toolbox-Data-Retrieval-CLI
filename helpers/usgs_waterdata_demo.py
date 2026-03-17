"""Helper module for the USGS Water Data demo notebook."""

from types import SimpleNamespace

import pandas as pd

try:
    from dataretrieval import waterdata as wd
except ImportError:  # pragma: no cover - monkeypatched in tests
    wd = SimpleNamespace(
        get_daily=None,
        get_monitoring_locations=None,
        get_time_series_metadata=None,
        get_field_measurements=None,
    )


DEMO_CONFIG = {
    "bbox": (-82.859, 31.899, -82.013, 32.947),
    "output_dir": "outputs/usgs_waterdata_demo",
    "date_range": ("1880-01-01", "2100-01-01"),
    "example_stations": {
        "discharge": {"station_id": "02225500", "parameter_code": "00060"},
        "gw_daily": {"station_id": "324209082430201", "parameter_code": "72019"},
        "gw_periodic": {"station_id": "410947071344803", "parameter_code": "72019"},
    },
}

LEGACY_CALLS = {
    "discharge": {
        "legacy_steps": ["New Project station discovery", "Adding Data to Project"],
    },
    "gw_daily": {
        "legacy_steps": ["New Project station discovery", "Adding Data to Project"],
    },
    "gw_periodic": {
        "legacy_steps": ["New Project station discovery", "Adding Data to Project"],
    },
}

NOTEBOOK_MAPPING_ROWS = [
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "discharge",
        "legacy_intent": "Find surface-water stations in a bounding box",
        "modern_helper_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=ST, parameter_code=00060",
        "expected_output_shape": "DataFrame of discharge-capable stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_daily",
        "legacy_intent": "Find groundwater stations with daily series in a bounding box",
        "modern_helper_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater daily stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Find groundwater stations with periodic observations in a bounding box",
        "modern_helper_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_field_measurements",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater periodic stations",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "discharge",
        "legacy_intent": "Retrieve discharge time series for a selected station",
        "modern_helper_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "parameter_code=00060, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_daily",
        "legacy_intent": "Retrieve groundwater daily time series for a selected station",
        "modern_helper_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Retrieve groundwater periodic measurements for a selected station",
        "modern_helper_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_field_measurements",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
]


def _normalize_station_frame(candidate_frame, qualifying_frame, workflow_type):
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

    return frame


def _get_discharge_stations(bbox):
    candidate_frame, _ = wd.get_monitoring_locations(bBox=bbox, site_type_code="ST")
    qualifying_frame, _ = wd.get_time_series_metadata(
        bBox=bbox,
        parameter_code="00060",
    )
    return _normalize_station_frame(candidate_frame, qualifying_frame, "discharge")


def _get_groundwater_daily_stations(bbox):
    candidate_frame, _ = wd.get_monitoring_locations(bBox=bbox, site_type_code="GW")
    qualifying_frame, _ = wd.get_time_series_metadata(
        bBox=bbox,
        site_type_code="GW",
    )
    return _normalize_station_frame(candidate_frame, qualifying_frame, "gw_daily")


def _get_groundwater_periodic_stations(bbox):
    candidate_frame, _ = wd.get_monitoring_locations(bBox=bbox, site_type_code="GW")
    qualifying_frame, _ = wd.get_field_measurements(bBox=bbox)
    return _normalize_station_frame(candidate_frame, qualifying_frame, "gw_periodic")


def get_usgs_stations_in_bbox(bbox, data_types):
    handlers = {
        "discharge": _get_discharge_stations,
        "gw_daily": _get_groundwater_daily_stations,
        "gw_periodic": _get_groundwater_periodic_stations,
    }
    return {workflow_type: handlers[workflow_type](bbox) for workflow_type in data_types}


def export_timeseries_artifacts(frame, output_dir, workflow_type, station_id):
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{workflow_type}_{station_id}.json"
    csv_path = output_dir / f"{workflow_type}_{station_id}.csv"
    parquet_path = output_dir / f"{workflow_type}_{station_id}.parquet"

    frame.to_json(json_path, orient="records", indent=2)
    frame.to_csv(csv_path, index=False)

    file_paths = {
        "json": json_path,
        "csv": csv_path,
        "parquet": parquet_path,
        "parquet_error": None,
    }
    try:
        frame.to_parquet(parquet_path, index=False)
    except Exception as exc:  # pragma: no cover - depends on parquet engine availability
        file_paths["parquet"] = None
        file_paths["parquet_error"] = str(exc)

    return file_paths


def get_usgs_timeseries(
    station_id,
    workflow_type,
    output_dir,
    parameter_code=None,
    date_range=("1880-01-01", "2100-01-01"),
):
    if workflow_type in {"discharge", "gw_daily"}:
        frame, metadata = wd.get_daily(
            monitoring_location_id=station_id,
            parameter_code="00060" if workflow_type == "discharge" else parameter_code,
            start=date_range[0],
            end=date_range[1],
        )
    elif workflow_type == "gw_periodic":
        frame, metadata = wd.get_field_measurements(
            monitoring_location_id=station_id,
            parameter_code=parameter_code,
            start=date_range[0],
            end=date_range[1],
        )
    else:
        raise ValueError(f"Unsupported workflow type: {workflow_type}")

    frame = frame.reset_index(drop=True).copy()
    frame["station_id"] = station_id
    frame["workflow_type"] = workflow_type

    if frame.empty:
        return {
            "frame": frame,
            "records": [],
            "files": {},
            "metadata": {**metadata, "warning": f"No records returned for {workflow_type} {station_id}"},
        }

    records = frame.to_dict(orient="records")
    file_paths = export_timeseries_artifacts(frame, output_dir, workflow_type, station_id)
    return {"frame": frame, "records": records, "files": file_paths, "metadata": metadata}
