"""Shared defaults and legacy mapping metadata for the sidecar package."""

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
        "modern_demo_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=ST, parameter_code=00060",
        "expected_output_shape": "DataFrame of discharge-capable stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_daily",
        "legacy_intent": "Find groundwater stations with daily series in a bounding box",
        "modern_demo_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater daily stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Find groundwater stations with periodic observations in a bounding box",
        "modern_demo_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_field_measurements",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater periodic stations",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "discharge",
        "legacy_intent": "Retrieve discharge time series for a selected station",
        "modern_demo_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "parameter_code=00060, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_daily",
        "legacy_intent": "Retrieve groundwater daily time series for a selected station",
        "modern_demo_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Retrieve groundwater periodic measurements for a selected station",
        "modern_demo_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_field_measurements",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
]
