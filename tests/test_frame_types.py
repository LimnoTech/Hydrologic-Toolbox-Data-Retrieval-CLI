"""Frame dtype helpers for memory-oriented Water Data outputs."""

from __future__ import annotations

import pandas as pd


def _is_category(series):
    return str(series.dtype) == "category"


def test_categorize_existing_columns_converts_only_requested_existing_columns():
    """Only named columns present on the frame should become categorical."""
    from waterdata_toolbox_demo.frame_types import categorize_existing_columns

    frame = pd.DataFrame(
        {
            "monitoring_location_id": ["USGS-1", "USGS-1", "USGS-2"],
            "parameter_code": ["00060", "00060", "72019"],
            "value": [1.0, 2.0, 3.0],
        }
    )

    result = categorize_existing_columns(
        frame,
        ["monitoring_location_id", "parameter_code", "missing_column"],
    )

    assert _is_category(result["monitoring_location_id"])
    assert _is_category(result["parameter_code"])
    assert result["value"].dtype == "float64"


def test_categorize_existing_columns_preserves_already_categorical_columns():
    """The helper should not disturb columns that are already categorical."""
    from waterdata_toolbox_demo.frame_types import categorize_existing_columns

    frame = pd.DataFrame(
        {
            "workflow_type": pd.Series(
                ["discharge", "gw_daily"],
                dtype=pd.CategoricalDtype(),
            )
        }
    )

    result = categorize_existing_columns(frame, ["workflow_type"])

    assert _is_category(result["workflow_type"])
    assert list(result["workflow_type"]) == ["discharge", "gw_daily"]


def test_get_usgs_timeseries_returns_categorical_repeated_columns(tmp_path):
    """Time-series payloads should categorize repeated codes before export/return."""
    from waterdata_toolbox_demo.timeseries import get_usgs_timeseries

    class FakeWaterdata:
        @staticmethod
        def get_daily(**kwargs):
            return (
                pd.DataFrame(
                    {
                        "time": ["2026-06-01", "2026-06-02"],
                        "value": [1.0, 2.0],
                        "monitoring_location_id": ["USGS-04193500", "USGS-04193500"],
                        "time_series_id": ["ts-1", "ts-1"],
                        "parameter_code": ["00060", "00060"],
                        "statistic_id": ["00003", "00003"],
                        "approval_status": ["Approved", "Approved"],
                        "qualifier": ["A", "A"],
                    }
                ),
                {},
            )

        @staticmethod
        def get_time_series_metadata(**kwargs):
            return (
                pd.DataFrame(
                    {
                        "time_series_id": ["ts-1"],
                        "monitoring_location_id": ["USGS-04193500"],
                        "parameter_code": ["00060"],
                        "statistic_id": ["00003"],
                        "parameter_description": ["Discharge, cubic feet per second"],
                    }
                ),
                {},
            )

        @staticmethod
        def get_monitoring_locations(**kwargs):
            return (
                pd.DataFrame(
                    {
                        "monitoring_location_id": ["USGS-04193500"],
                        "monitoring_location_number": ["04193500"],
                        "monitoring_location_name": ["MAUMEE RIVER AT WATERVILLE OH"],
                        "hydrologic_unit_code": ["04100009"],
                    }
                ),
                {},
            )

    payload = get_usgs_timeseries(
        "04193500",
        "discharge",
        tmp_path,
        waterdata_module=FakeWaterdata,
    )

    frame = payload["frame"]

    assert _is_category(frame["monitoring_location_id"])
    assert _is_category(frame["parameter_code"])
    assert _is_category(frame["statistic_id"])
    assert _is_category(frame["approval_status"])
    assert _is_category(frame["qualifier"])
    assert _is_category(frame["station_id"])
    assert _is_category(frame["workflow_type"])
    assert frame["value"].dtype == "float64"


def test_normalize_station_frame_returns_categorical_station_columns(monkeypatch):
    """Station discovery should categorize repeated station metadata before export."""
    from waterdata_toolbox_demo import station_discovery

    candidate_frame = pd.DataFrame(
        {
            "agency_code": ["USGS", "USGS", "USGS"],
            "monitoring_location_id": ["USGS-2", "USGS-1", "USGS-1"],
            "monitoring_location_number": ["2", "1", "1"],
            "monitoring_location_name": ["Station 2", "Station 1", "Station 1"],
            "site_type_code": ["ST", "ST", "ST"],
            "hydrologic_unit_code": ["04100009", "04100009", "04100009"],
            "longitude": [-83.7, -83.6, -83.6],
            "latitude": [41.5, 41.4, 41.4],
        }
    )
    qualifying_frame = pd.DataFrame(
        {"monitoring_location_id": ["USGS-1", "USGS-2"]}
    )
    monkeypatch.setattr(
        station_discovery,
        "_to_station_geodataframe",
        lambda frame: frame,
    )

    result = station_discovery._normalize_station_frame(
        candidate_frame,
        qualifying_frame,
        "discharge",
    )

    assert _is_category(result["agency_code"])
    assert _is_category(result["monitoring_location_id"])
    assert _is_category(result["monitoring_location_number"])
    assert _is_category(result["monitoring_location_name"])
    assert _is_category(result["site_type_code"])
    assert _is_category(result["hydrologic_unit_code"])
    assert result["longitude"].dtype == "float64"
    assert result["latitude"].dtype == "float64"
