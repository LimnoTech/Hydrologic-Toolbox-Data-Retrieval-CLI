from pathlib import Path
import json

from helpers.usgs_waterdata_demo import DEMO_CONFIG, LEGACY_CALLS, NOTEBOOK_MAPPING_ROWS


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
