"""Validation for the active CLI-only package surface."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def test_app_routes_to_cli_help_when_no_args(monkeypatch):
    """The active app entrypoint should route empty args to CLI help."""
    from waterdata_toolbox_demo import app

    calls = []

    monkeypatch.setattr(app, "run_cli", lambda argv: calls.append(list(argv)) or 0)

    result = app.main([])

    assert result == 0
    assert calls == [["--help"]]


def test_active_app_surface_has_no_run_gui():
    """The active product surface should not expose GUI routing helpers."""
    from waterdata_toolbox_demo import app

    assert not hasattr(app, "run_gui")


def test_gui_module_lives_in_sandbox():
    """Legacy GUI code should move under sandbox rather than stay in the active package."""
    assert not (PROJECT_ROOT / "src" / "waterdata_toolbox_demo" / "gui.py").exists()
    assert (PROJECT_ROOT / "sandbox" / "src" / "waterdata_toolbox_demo" / "gui.py").exists()


def test_create_new_project_parser_accepts_repeatable_wf():
    """Create-new-project should use repeatable --wf options."""
    from waterdata_toolbox_demo.cli import build_parser

    args = build_parser().parse_args(
        ["create-new-project", "--wf", "discharge", "--wf", "daily"]
    )

    assert args.command == "create-new-project"
    assert args.wf == ["discharge", "daily"]


def test_add_data_parser_accepts_positional_workflow():
    """Add-data should take its workflow as a required positional argument."""
    from waterdata_toolbox_demo.cli import build_parser

    args = build_parser().parse_args(
        ["add-data", "discharge", "--station-id", "02225500", "--parameter-code", "00060"]
    )

    assert args.command == "add-data"
    assert args.workflow == "discharge"


def test_create_new_project_help_shows_wf_and_not_old_flags(capsys):
    """Create-new-project help should advertise --wf instead of workflow booleans."""
    from waterdata_toolbox_demo.cli import build_parser

    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["create-new-project", "--help"])

    help_text = capsys.readouterr().out

    assert "--wf {discharge,daily,periodic}" in help_text
    assert "--discharge" not in help_text
    assert "--daily" not in help_text
    assert "--periodic" not in help_text


def test_add_data_help_shows_positional_workflow_and_not_old_flags(capsys):
    """Add-data help should advertise a positional workflow instead of booleans."""
    from waterdata_toolbox_demo.cli import build_parser

    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["add-data", "--help"])

    help_text = capsys.readouterr().out

    assert "{discharge,daily,periodic}" in help_text
    assert "Workflow to run." in help_text
    assert "--discharge" not in help_text
    assert "--daily" not in help_text
    assert "--periodic" not in help_text
