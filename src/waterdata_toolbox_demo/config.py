"""Shared defaults for the packaged Water Data ToolBox app."""

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
