"""Local validation tests for the csv-output branch package behavior."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


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

        @staticmethod
        def get_monitoring_locations(*, monitoring_location_id):
            return (
                pd.DataFrame(
                    [{"monitoring_location_id": monitoring_location_id, "site_type_code": "ST"}]
                ),
                {"source": "monitoring-locations"},
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


def test_create_project_csv_artifacts(tmp_path, monkeypatch):
    """Create-new-project should write one CSV artifact per selected workflow."""
    from waterdata_toolbox_demo import station_discovery

    monkeypatch.setattr(station_discovery, "_to_station_geodataframe", lambda frame: frame)

    bbox = (-82.859, 31.899, -82.013, 32.947)
    discharge_candidates = pd.DataFrame(
        [
            {
                "monitoring_location_id": "USGS-11111111",
                "monitoring_location_number": "11111111",
                "monitoring_location_name": "River A",
                "site_type_code": "ST",
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

    results = station_discovery.run_create_new_project_section(
        bbox,
        ["discharge", "gw_periodic"],
        tmp_path,
        waterdata_module=DummyWaterData,
    )

    discharge_files = results["discharge"]["files"]
    periodic_files = results["gw_periodic"]["files"]

    assert set(discharge_files) == {"csv"}
    assert set(periodic_files) == {"csv"}
    assert discharge_files["csv"].name == "create_new_project_discharge.csv"
    assert periodic_files["csv"].name == "create_new_project_gw_periodic.csv"
    assert results["discharge"]["artifact_messages"] == [str(discharge_files["csv"])]
    assert results["gw_periodic"]["artifact_messages"] == [str(periodic_files["csv"])]
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "create_new_project_discharge.csv",
        "create_new_project_gw_periodic.csv",
    ]


def test_package_build_docs_describe_csv_only_windows_app():
    """Package docs and build metadata should describe the CSV-only packaged app."""
    package_doc = (
        PROJECT_ROOT / "src" / "waterdata_toolbox_demo" / "waterdata-package-cli-gui.md"
    ).read_text(encoding="utf-8")
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    spec_text = (PROJECT_ROOT / "waterdata_toolbox_demo.spec").read_text(encoding="utf-8")

    assert "CSV-only" in package_doc
    assert "pyinstaller waterdata_toolbox_demo.spec" in package_doc
    assert "notebook" not in package_doc.lower()
    assert "json artifact" not in package_doc.lower()
    assert "parquet" not in package_doc.lower()
    assert 'readme = "src/waterdata_toolbox_demo/waterdata-package-cli-gui.md"' in pyproject_text
    assert '"pyarrow"' not in pyproject_text
    assert "waterdata_toolbox_demo.plotting" not in spec_text
