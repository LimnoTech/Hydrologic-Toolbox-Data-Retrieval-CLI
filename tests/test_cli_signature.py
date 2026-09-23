"""CLI signature and live endpoint coverage for the active packaged app."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _cli_env() -> dict[str, str]:
    """Return an environment that exposes the active package on PYTHONPATH."""
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{SRC_DIR}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(SRC_DIR)
    )
    return env


def run_cli_command(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI entrypoint as a subprocess and capture stdout/stderr."""
    return subprocess.run(
        [sys.executable, "-m", "hydrologic_toolbox_data_retrieval_cli", *args],
        cwd=PROJECT_ROOT,
        env=_cli_env(),
        capture_output=True,
        text=True,
    )


def assert_shapefile_set_exists(output_dir: Path, stem: str) -> None:
    """Assert that one shapefile set and all sidecars were written."""
    for suffix in (".shp", ".shx", ".dbf", ".prj", ".cpg"):
        assert (output_dir / f"{stem}{suffix}").exists()


def read_first_lines(path: Path, count: int = 3) -> list[str]:
    """Return the first few lines of a text file without trailing newlines."""
    with path.open(encoding="utf-8") as handle:
        return [handle.readline().rstrip("\n") for _ in range(count)]


# Offline parser and error coverage


def test_no_args_routes_to_help_and_returns_zero(capsys):
    """The packaged app should print help and return zero on empty args."""
    from hydrologic_toolbox_data_retrieval_cli import app

    result = app.main([])
    output = capsys.readouterr().out

    assert result == 0
    assert "usage: hydrologic-toolbox-data-retrieval-cli" in output


def test_create_new_project_parser_accepts_repeatable_wf():
    """Create-new-project should accept one or more repeatable --wf flags."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    args = build_parser().parse_args(
        [
            "create-new-project",
            "--wf",
            "discharge",
            "--wf",
            "gw_daily",
            "--bbox",
            "-82.859",
            "31.899",
            "-82.013",
            "32.947",
        ]
    )

    assert args.command == "create-new-project"
    assert args.wf == ["discharge", "gw_daily"]


def test_add_data_parser_accepts_positional_workflow():
    """Add-data should accept one required positional workflow argument."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    args = build_parser().parse_args(
        ["add-data", "discharge", "--station-id", "02225500"]
    )

    assert args.command == "add-data"
    assert args.workflow == "discharge"


def test_run_cli_command_uses_current_python_interpreter(monkeypatch):
    """CLI subprocesses should run under the same interpreter as pytest."""
    captured: dict[str, object] = {}
    sentinel_python = "/tmp/current-python"

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "executable", sentinel_python)

    result = run_cli_command("add-data", "discharge", "--station-id", "02225500")

    assert result.returncode == 0
    assert captured["command"][0] == sentinel_python


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["create-new-project"],
        ["create-new-project", "--wf", "bogus"],
        ["create-new-project", "--wf", "discharge"],
        ["create-new-project", "--wf", "discharge", "--bbox", "-82.859", "31.899", "-82.013"],
        ["create-new-project", "--wf", "discharge", "--unknown"],
    ],
    ids=[
        "missing_subcommand",
        "create_new_project_missing_wf",
        "create_new_project_bad_wf",
        "create_new_project_missing_bbox",
        "create_new_project_short_bbox",
        "create_new_project_unknown_flag",
    ],
)
def test_invalid_create_new_project_parser_cases(argv):
    """Invalid create-new-project command shapes should fail before any network work."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(argv)

    assert exc_info.value.code == 2


@pytest.mark.parametrize(
    "argv",
    [
        ["add-data"],
        ["add-data", "bogus"],
        ["add-data", "discharge", "extra"],
        ["add-data", "discharge", "--unknown"],
    ],
    ids=[
        "add_data_missing_workflow",
        "add_data_bad_workflow",
        "add_data_unexpected_extra_positional",
        "add_data_unknown_flag",
    ],
)
def test_invalid_add_data_parser_cases(argv):
    """Invalid add-data command shapes should fail before any network work."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    with pytest.raises(SystemExit) as exc_info:
        build_parser().parse_args(argv)

    assert exc_info.value.code == 2


def test_help_surface_for_create_new_project(capsys):
    """Create-new-project help should advertise --wf instead of legacy booleans."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["create-new-project", "--help"])

    help_text = capsys.readouterr().out

    assert exc_info.value.code == 0
    assert "--wf {discharge,gw_daily,gw_periodic}" in help_text
    assert "--discharge" not in help_text
    assert "--daily" not in help_text
    assert "--periodic" not in help_text


def test_help_surface_for_add_data(capsys):
    """Add-data help should advertise the positional workflow surface."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["add-data", "--help"])

    help_text = capsys.readouterr().out

    assert exc_info.value.code == 0
    assert "{discharge,gw_daily,gw_periodic}" in help_text
    assert "Workflow to run." in help_text
    assert "--discharge" not in help_text
    assert "--parameter-code" not in help_text


# Live create-new-project coverage


@pytest.mark.live
@pytest.mark.parametrize(
    ("workflow_values", "expected_stems", "expected_labels"),
    [
        (["discharge"], ["discharge"], ["discharge"]),
        (["gw_daily"], ["daily"], ["gw_daily"]),
        (["gw_periodic"], ["periodic"], ["gw_periodic"]),
        (["discharge", "gw_daily"], ["discharge", "daily"], ["discharge", "gw_daily"]),
        (["discharge", "gw_periodic"], ["discharge", "periodic"], ["discharge", "gw_periodic"]),
        (["gw_daily", "gw_periodic"], ["daily", "periodic"], ["gw_daily", "gw_periodic"]),
        (
            ["discharge", "gw_daily", "gw_periodic"],
            ["discharge", "daily", "periodic"],
            ["discharge", "gw_daily", "gw_periodic"],
        ),
    ],
    ids=[
        "create_new_project_discharge_live",
        "create_new_project_gw_daily_live",
        "create_new_project_gw_periodic_live",
        "create_new_project_discharge_gw_daily_live",
        "create_new_project_discharge_gw_periodic_live",
        "create_new_project_gw_daily_gw_periodic_live",
        "create_new_project_all_live",
    ],
)
def test_live_create_new_project_workflow_combinations(
    tmp_path: Path,
    workflow_values: list[str],
    expected_stems: list[str],
    expected_labels: list[str],
):
    """Every non-empty workflow combination should succeed and write shapefiles."""
    output_dir = tmp_path / ("create_new_project_" + "_".join(workflow_values))
    args = ["create-new-project"]
    for workflow in workflow_values:
        args.extend(["--wf", workflow])
    args.extend(["--bbox", "-82.859", "31.899", "-82.013", "32.947"])
    args.extend(["--output-dir", str(output_dir)])

    result = run_cli_command(*args)

    assert result.returncode == 0, result.stderr or result.stdout
    for label in expected_labels:
        assert re.search(rf"{re.escape(label)}: \d+ stations", result.stdout), result.stdout
    for stem in expected_stems:
        assert_shapefile_set_exists(output_dir, stem)


@pytest.mark.live
def test_live_create_new_project_periodic_bbox_override(tmp_path: Path):
    """A bounded periodic create-new-project run should still succeed."""
    output_dir = tmp_path / "create_new_project_periodic_bbox"
    result = run_cli_command(
        "create-new-project",
        "--wf",
        "gw_periodic",
        "--bbox",
        "-82.859",
        "31.899",
        "-82.013",
        "32.947",
        "--output-dir",
        str(output_dir),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert re.search(r"gw_periodic: \d+ stations", result.stdout), result.stdout
    assert_shapefile_set_exists(output_dir, "periodic")


# Live add-data coverage


@pytest.mark.live
@pytest.mark.parametrize(
    (
        "workflow",
        "station_id",
        "date_range",
        "expected_file_name",
        "expected_label",
        "uses_reduced_header",
    ),
    [
        (
            "discharge",
            "02225500",
            None,
            "discharge_02225500.csv",
            "discharge",
            True,
        ),
        (
            "gw_daily",
            "324209082430201",
            None,
            "gw_daily_324209082430201.csv",
            "gw_daily",
            True,
        ),
        (
            "gw_periodic",
            "410947071344803",
            ("1880-01-01", "2100-01-01"),
            "gw_periodic_410947071344803.csv",
            "gw_periodic",
            False,
        ),
    ],
    ids=[
        "add_data_discharge_live",
        "add_data_gw_daily_live",
        "add_data_gw_periodic_live",
    ],
)
def test_live_add_data_workflows(
    tmp_path: Path,
    workflow: str,
    station_id: str,
    date_range: tuple[str, str] | None,
    expected_file_name: str,
    expected_label: str,
    uses_reduced_header: bool,
):
    """Each valid add-data workflow should succeed and write the expected CSV."""
    output_dir = tmp_path / f"add_data_{workflow}"
    args = [
        "add-data",
        workflow,
        "--station-id",
        station_id,
    ]
    if date_range is not None:
        args.extend(["--start-date", date_range[0], "--end-date", date_range[1]])
    args.extend(["--output-dir", str(output_dir)])

    result = run_cli_command(*args)

    assert result.returncode == 0, result.stderr or result.stdout
    assert re.search(rf"{re.escape(expected_label)}: \d+ rows", result.stdout), result.stdout

    csv_path = output_dir / expected_file_name
    assert csv_path.exists()

    if uses_reduced_header:
        lines = read_first_lines(csv_path)
        assert (
            lines[0]
            == "# site_no,Description,Parameter,Statistic,TS_ID,IV_TS_ID,Site number,Station name,Latitude,Longitude,HUC code,Drainage area"
        )
        assert lines[1].startswith("# ")
        assert lines[2] == "Time,Daily values,Approval status,Qualifier"
        assert len(csv_path.read_text(encoding="utf-8").splitlines()) > 3
    else:
        lines = read_first_lines(csv_path)
        assert lines[0].startswith("# monitoring_location_id")
        assert lines[1].startswith("# ")
        assert lines[2].startswith("time,value")
        assert "station_id" not in lines[2]
        assert "workflow_type" not in lines[2]
