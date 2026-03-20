from pathlib import Path
import json

import pandas as pd

from helpers.usgs_waterdata_demo import DEMO_CONFIG, LEGACY_CALLS, NOTEBOOK_MAPPING_ROWS
from helpers.usgs_waterdata_demo import get_usgs_stations_in_bbox
from helpers.usgs_waterdata_demo import export_timeseries_artifacts, get_usgs_timeseries


ROOT = Path(__file__).resolve().parents[1]


def test_expected_demo_files_exist():
    expected_paths = [
        ROOT / "helpers" / "__init__.py",
        ROOT / "helpers" / "usgs_waterdata_demo.py",
        ROOT / "notebooks" / "usgs_waterdata_demo.ipynb",
        ROOT / "requirements.txt",
        ROOT / "outputs" / "usgs_waterdata_demo" / ".gitkeep",
    ]

    for path in expected_paths:
        assert path.exists(), f"Expected demo file to exist: {path}"


def test_demo_config_and_mapping_cover_all_workflow_types():
    core_keys = {
        "legacy_workflow_step",
        "workflow_type",
        "legacy_intent",
        "modern_helper_entry_point",
        "waterdata_calls",
        "important_filters",
        "expected_output_shape",
    }

    assert set(DEMO_CONFIG["example_stations"]) == {"discharge", "gw_daily", "gw_periodic"}
    assert set(LEGACY_CALLS) == {"discharge", "gw_daily", "gw_periodic"}
    assert DEMO_CONFIG["date_range"] == ("1880-01-01", "2100-01-01")
    assert len(NOTEBOOK_MAPPING_ROWS) == 6
    assert {row["workflow_type"] for row in NOTEBOOK_MAPPING_ROWS} == {
        "discharge",
        "gw_daily",
        "gw_periodic",
    }
    assert {row["legacy_workflow_step"] for row in NOTEBOOK_MAPPING_ROWS} == {
        "New Project station discovery",
        "Adding Data to Project",
    }
    assert all(core_keys <= set(row) for row in NOTEBOOK_MAPPING_ROWS)


def test_demo_notebook_surfaces_mapping_rows_table():
    notebook = json.loads((ROOT / "notebooks" / "usgs_waterdata_demo.ipynb").read_text())
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    sources = ["".join(cell.get("source", [])) for cell in code_cells]

    assert any("import pandas as pd" in source for source in sources)
    assert any("pd.DataFrame(NOTEBOOK_MAPPING_ROWS)" in source for source in sources)


def test_station_discovery_intersects_service_results_and_tags_workflow(monkeypatch):
    monitoring_calls = []
    metadata_calls = []
    field_calls = []

    def fake_monitoring_locations(**kwargs):
        monitoring_calls.append(kwargs)
        if kwargs["site_type_code"] == "ST":
            frame = pd.DataFrame(
                [
                    {
                        "monitoring_location_id": "USGS-1",
                        "location_name": "Surface One",
                        "site_type_code": "ST",
                    },
                    {
                        "monitoring_location_id": "USGS-9",
                        "location_name": "Surface Nine",
                        "site_type_code": "ST",
                    },
                ]
            )
        else:
            frame = pd.DataFrame(
                [
                    {
                        "monitoring_location_id": "USGS-2",
                        "location_name": "GW Two",
                        "site_type_code": "GW",
                    },
                    {
                        "monitoring_location_id": "USGS-3",
                        "location_name": "GW Three",
                        "site_type_code": "GW",
                    },
                ]
            )
        return frame, {}

    def fake_metadata(**kwargs):
        metadata_calls.append(kwargs)
        if kwargs.get("parameter_code") == "00060":
            frame = pd.DataFrame([{"monitoring_location_id": "USGS-1"}])
        else:
            frame = pd.DataFrame([{"monitoring_location_id": "USGS-2"}])
        return frame, {}

    def fake_field_measurements(**kwargs):
        field_calls.append(kwargs)
        return pd.DataFrame([{"monitoring_location_id": "USGS-3"}]), {}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_monitoring_locations", fake_monitoring_locations)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_time_series_metadata", fake_metadata)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_field_measurements", fake_field_measurements)

    result = get_usgs_stations_in_bbox(
        (-82.859, 31.899, -82.013, 32.947),
        ["discharge", "gw_daily", "gw_periodic"],
    )

    assert set(result) == {"discharge", "gw_daily", "gw_periodic"}
    assert result["discharge"]["monitoring_location_id"].tolist() == ["USGS-1"]
    assert result["gw_daily"]["monitoring_location_id"].tolist() == ["USGS-2"]
    assert result["gw_periodic"]["monitoring_location_id"].tolist() == ["USGS-3"]
    assert set(["workflow_type", "monitoring_location_id"]) <= set(result["discharge"].columns)
    assert monitoring_calls[0]["site_type_code"] == "ST"
    assert monitoring_calls[1]["site_type_code"] == "GW"
    assert metadata_calls[0]["parameter_code"] == "00060"
    assert field_calls[0]["bBox"] == (-82.859, 31.899, -82.013, 32.947)


def test_station_discovery_returns_empty_frame_when_no_candidates_match(monkeypatch):
    def fake_monitoring_locations(**kwargs):
        return pd.DataFrame([{"monitoring_location_id": "USGS-9"}]), {}

    def fake_metadata(**kwargs):
        return pd.DataFrame([{"monitoring_location_id": "USGS-1"}]), {}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_monitoring_locations", fake_monitoring_locations)
    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_time_series_metadata", fake_metadata)

    result = get_usgs_stations_in_bbox((-82.859, 31.899, -82.013, 32.947), ["discharge"])

    assert result["discharge"].empty
    assert "workflow_type" in result["discharge"].columns


def test_timeseries_routes_expected_service_calls_and_returns_contract(monkeypatch, tmp_path):
    calls = []

    def fake_daily(**kwargs):
        calls.append(("daily", kwargs))
        return pd.DataFrame([{"value": 1.0, "observation_time": "2020-01-01"}]), {
            "source": "daily"
        }

    def fake_field_measurements(**kwargs):
        calls.append(("field", kwargs))
        return pd.DataFrame([{"value": 2.0, "observation_time": "2020-01-02"}]), {
            "source": "field"
        }

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)
    monkeypatch.setattr(
        "helpers.usgs_waterdata_demo.wd.get_field_measurements",
        fake_field_measurements,
    )

    discharge_payload = get_usgs_timeseries("02225500", "discharge", tmp_path)
    gw_daily_payload = get_usgs_timeseries(
        "324209082430201",
        "gw_daily",
        tmp_path,
        parameter_code="72019",
    )
    gw_periodic_payload = get_usgs_timeseries(
        "410947071344803",
        "gw_periodic",
        tmp_path,
        parameter_code="72019",
    )

    assert [name for name, _ in calls] == ["daily", "daily", "field"]
    assert calls[0][1]["parameter_code"] == "00060"
    assert calls[1][1]["parameter_code"] == "72019"
    assert calls[0][1]["start"] == "1880-01-01"
    assert calls[0][1]["end"] == "2100-01-01"
    assert discharge_payload["records"][0]["workflow_type"] == "discharge"
    assert gw_daily_payload["records"][0]["workflow_type"] == "gw_daily"
    assert gw_periodic_payload["records"][0]["workflow_type"] == "gw_periodic"
    assert {"frame", "records", "files", "metadata"} <= set(discharge_payload)


def test_export_writes_json_and_csv_and_tracks_parquet(tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].exists()
    assert file_paths["csv"].exists()
    assert "parquet" in file_paths
    loaded = json.loads(file_paths["json"].read_text())
    assert loaded[0]["station_id"] == "A"


def test_export_keeps_json_and_csv_when_parquet_is_unavailable(monkeypatch, tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    def fake_to_parquet(*args, **kwargs):
        raise ImportError("Missing optional dependency 'pyarrow'")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].exists()
    assert file_paths["csv"].exists()
    assert file_paths["parquet"] is None
    assert "pyarrow" in file_paths["parquet_error"]


def test_export_uses_deterministic_filenames(tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].name == "discharge_A.json"
    assert file_paths["csv"].name == "discharge_A.csv"


def test_timeseries_returns_empty_frame_contract_when_service_has_no_rows(
    monkeypatch, tmp_path
):
    def fake_daily(**kwargs):
        return pd.DataFrame(columns=["value"]), {"source": "daily"}

    monkeypatch.setattr("helpers.usgs_waterdata_demo.wd.get_daily", fake_daily)

    payload = get_usgs_timeseries("02225500", "discharge", tmp_path)

    assert payload["frame"].empty
    assert payload["records"] == []
    assert payload["metadata"]["source"] == "daily"
