"""Local validation tests for the csv-output branch package behavior."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def test_app_routes_to_cli_help_when_no_args(monkeypatch):
    """The packaged app should print CLI help instead of launching the GUI."""
    from waterdata_toolbox_demo import app

    calls = []

    monkeypatch.setattr(app, "run_cli", lambda argv: calls.append(list(argv)) or 0)
    monkeypatch.setattr(
        app,
        "run_gui",
        lambda: (_ for _ in ()).throw(AssertionError("GUI should not run")),
    )

    result = app.main([])

    assert result == 0
    assert calls == [["--help"]]


def test_cli_parser_accepts_create_new_project_workflow_flags():
    """Create-new-project should accept one or more human-facing workflow flags."""
    from waterdata_toolbox_demo.cli import build_parser

    args = build_parser().parse_args(["create-new-project", "--discharge", "--daily"])

    assert args.command == "create-new-project"
    assert args.discharge is True
    assert args.daily is True
    assert args.periodic is False


def test_run_cli_requires_create_new_project_workflow_flag(monkeypatch):
    """Create-new-project should require at least one workflow flag."""
    from waterdata_toolbox_demo import cli

    monkeypatch.setattr(
        cli,
        "run_create_new_project_section",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("station discovery should not run")
        ),
    )

    with pytest.raises(SystemExit):
        cli.run_cli(["create-new-project"])


def test_cli_parser_accepts_add_data_workflow_flag():
    """Add-data should accept the new single-workflow flags."""
    from waterdata_toolbox_demo.cli import build_parser

    args = build_parser().parse_args(["add-data", "--discharge"])

    assert args.command == "add-data"
    assert args.discharge is True
    assert args.daily is False
    assert args.periodic is False


def test_run_cli_rejects_multiple_add_data_workflow_flags(monkeypatch):
    """Add-data should reject multiple workflow flags in one call."""
    from waterdata_toolbox_demo import cli

    monkeypatch.setattr(
        cli,
        "get_usgs_timeseries",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("timeseries retrieval should not run")
        ),
    )

    with pytest.raises(SystemExit):
        cli.run_cli(["add-data", "--discharge", "--daily"])


def test_add_data_csv_only_artifacts(tmp_path):
    """Add-data should persist only the CSV artifact for packaged app runs."""
    from waterdata_toolbox_demo.exports import format_artifact_messages
    from waterdata_toolbox_demo.timeseries import get_usgs_timeseries

    class DummyWaterData:
        @staticmethod
        def get_daily(*, monitoring_location_id, parameter_code, time):
            return (
                pd.DataFrame(
                    [
                        {
                            "monitoring_location_id": monitoring_location_id,
                            "time": "2024-01-01",
                            "value": 1.5,
                            "approval_status": "Approved",
                            "qualifier": None,
                            "parameter_code": parameter_code,
                            "statistic_id": "00003",
                            "time_series_id": "daily-ts-id",
                        }
                    ]
                ),
                {"source": "daily"},
            )

        @staticmethod
        def get_time_series_metadata(*, monitoring_location_id, parameter_code):
            return (
                pd.DataFrame(
                    [
                        {
                            "monitoring_location_id": monitoring_location_id,
                            "parameter_code": parameter_code,
                            "parameter_description": "Discharge, cubic feet per second",
                            "parent_time_series_id": "iv-ts-id",
                            "statistic_id": "00003",
                            "time_series_id": "daily-ts-id",
                        }
                    ]
                ),
                {"source": "timeseries-metadata"},
            )

    payload = get_usgs_timeseries(
        "02225500",
        "discharge",
        tmp_path,
        parameter_code="00060",
        waterdata_module=DummyWaterData,
    )

    assert set(payload["files"]) == {"csv"}
    assert payload["files"]["csv"].name == "discharge_02225500.csv"
    assert format_artifact_messages(payload["files"]) == [str(payload["files"]["csv"])]
    assert [path.name for path in tmp_path.iterdir()] == ["discharge_02225500.csv"]


def test_create_project_shapefile_artifacts(tmp_path):
    """Create-new-project should write one shapefile per selected workflow."""
    from waterdata_toolbox_demo.station_discovery import run_create_new_project_section

    discharge_candidates = pd.DataFrame(
        [
            {
                "monitoring_location_id": "USGS-11111111",
                "monitoring_location_number": "11111111",
                "monitoring_location_name": "River A",
                "site_type_code": "ST",
                "agency_code": "USGS",
                "hydrologic_unit_code": "03060201",
                "state_code": "13",
                "county_code": "163",
                "latitude": 31.9,
                "longitude": -82.8,
            }
        ]
    )
    groundwater_candidates = pd.DataFrame(
        [
            {
                "monitoring_location_id": "USGS-33333333",
                "monitoring_location_number": "33333333",
                "monitoring_location_name": "Well Periodic",
                "site_type_code": "GW",
                "agency_code": "USGS",
                "hydrologic_unit_code": "03060202",
                "state_code": "13",
                "county_code": "001",
                "latitude": 32.0,
                "longitude": -82.6,
            }
        ]
    )

    class DummyWaterData:
        @staticmethod
        def get_monitoring_locations(*, bbox, site_type_code):
            if site_type_code == "ST":
                return discharge_candidates, {"source": "candidate"}
            return groundwater_candidates, {"source": "candidate"}

        @staticmethod
        def get_time_series_metadata(*, bbox, parameter_code=None):
            return (
                pd.DataFrame([{"monitoring_location_id": "USGS-11111111"}]),
                {"source": "qualifying"},
            )

        @staticmethod
        def get_field_measurements(*, bbox):
            return (
                pd.DataFrame([{"monitoring_location_id": "USGS-33333333"}]),
                {"source": "qualifying"},
            )

    results = run_create_new_project_section(
        (-82.859, 31.899, -82.013, 32.947),
        ["discharge", "gw_periodic"],
        tmp_path,
        waterdata_module=DummyWaterData,
    )

    discharge_path = results["discharge"]["files"]["shp"]
    periodic_path = results["gw_periodic"]["files"]["shp"]

    assert discharge_path.name == "discharge.shp"
    assert periodic_path.name == "periodic.shp"
    assert results["discharge"]["artifact_messages"] == [str(discharge_path)]
    assert results["gw_periodic"]["artifact_messages"] == [str(periodic_path)]
    for path in (discharge_path, periodic_path):
        assert path.exists()
        assert path.with_suffix(".dbf").exists()
        assert path.with_suffix(".shx").exists()
        assert path.with_suffix(".prj").exists()


def test_export_station_shapefile_artifacts_reduce_fields(tmp_path):
    """Station shapefiles should keep only the reduced schema plus geometry."""
    import geopandas as gpd
    from shapely.geometry import Point

    from waterdata_toolbox_demo.exports import export_station_shapefile_artifacts

    frame = gpd.GeoDataFrame(
        [
            {
                "site_no": "02225500",
                "monitoring_location_id": "USGS-02225500",
                "station_nm": "OHOOPEE RIVER NEAR REIDSVILLE, GA",
                "site_tp_cd": "ST",
                "state_cd": "13",
                "county_cd": "267",
                "dec_lat_va": 32.0771388888889,
                "dec_long_va": -82.1765,
                "agency_code": "USGS",
                "hydrologic_unit_code": "03060201",
                "unused_column": "drop-me",
                "geometry": Point(-82.1765, 32.0771388888889),
            }
        ],
        geometry="geometry",
        crs="EPSG:4326",
    )

    files = export_station_shapefile_artifacts(frame, tmp_path, "discharge")
    result = gpd.read_file(files["shp"])

    assert list(result.columns) == [
        "site_no",
        "loc_id",
        "stn_name",
        "site_tp",
        "state_cd",
        "county_cd",
        "lat",
        "lon",
        "agency_cd",
        "huc_code",
        "geometry",
    ]


def test_package_build_docs_describe_cli_only_shapefile_app():
    """Package docs and build metadata should describe the CLI-only shapefile app."""
    package_doc = (
        PROJECT_ROOT / "src" / "waterdata_toolbox_demo" / "waterdata-package-cli-gui.md"
    ).read_text(encoding="utf-8")
    shapefile_note = (
        PROJECT_ROOT / "docs" / "create-new-project-shapefile-fields.md"
    ).read_text(encoding="utf-8")

    assert "CLI-only" in package_doc
    assert "create-new-project" in package_doc
    assert "discharge.shp" in package_doc
    assert "GUI launch" not in package_doc
    assert "site_no" in shapefile_note
    assert "Excluded columns" in shapefile_note
