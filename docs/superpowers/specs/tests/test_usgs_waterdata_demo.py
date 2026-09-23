from __future__ import annotations

from pathlib import Path
import json
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_ROOT = ROOT / "sandbox"
if str(SANDBOX_ROOT) not in sys.path:
    sys.path.insert(0, str(SANDBOX_ROOT))

from helpers.usgs_waterdata_demo import DEMO_CONFIG, LEGACY_CALLS, NOTEBOOK_MAPPING_ROWS
from helpers.usgs_waterdata_demo import export_timeseries_artifacts, format_artifact_messages


def test_expected_legacy_demo_files_exist_in_sandbox():
    expected_paths = [
        ROOT / "sandbox" / "helpers" / "__init__.py",
        ROOT / "sandbox" / "helpers" / "usgs_waterdata_demo.py",
        ROOT / "sandbox" / "notebooks" / "usgs_waterdata_demo.ipynb",
        ROOT / "requirements.txt",
        ROOT / "outputs" / "usgs_waterdata_demo" / ".gitkeep",
    ]

    for path in expected_paths:
        assert path.exists(), f"Expected legacy demo file to exist: {path}"


def test_sandbox_demo_config_and_mapping_rows_still_exist():
    core_keys = {
        "legacy_workflow_step",
        "workflow_type",
        "legacy_intent",
        "modern_demo_entry_point",
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
    assert all(core_keys <= set(row) for row in NOTEBOOK_MAPPING_ROWS)


def test_sandbox_demo_notebook_surfaces_mapping_rows_table():
    notebook = json.loads(
        (ROOT / "sandbox" / "notebooks" / "usgs_waterdata_demo.ipynb").read_text()
    )
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    sources = ["".join(cell.get("source", [])) for cell in code_cells]

    assert any("import pandas as pd" in source for source in sources)
    assert any("pd.DataFrame(NOTEBOOK_MAPPING_ROWS)" in source for source in sources)


def test_sandbox_export_writes_json_and_csv_and_tracks_parquet(tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")

    assert file_paths["json"].exists()
    assert file_paths["csv"].exists()
    assert "parquet" in file_paths
    loaded = json.loads(file_paths["json"].read_text())
    assert loaded[0]["station_id"] == "A"


def test_sandbox_format_artifact_messages_reports_written_paths(tmp_path):
    frame = pd.DataFrame([{"station_id": "A", "workflow_type": "discharge", "value": 1.0}])

    file_paths = export_timeseries_artifacts(frame, tmp_path, "discharge", "A")
    messages = format_artifact_messages(file_paths)

    assert str(file_paths["json"]) in messages
    assert str(file_paths["csv"]) in messages
