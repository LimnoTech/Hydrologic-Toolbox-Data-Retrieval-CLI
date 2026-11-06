"""The pure parts of ``scripts/measure_bundle.py``."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "measure_bundle.py"


def _load_script():
    """Import the script by path; ``scripts/`` is not a package."""
    spec = importlib.util.spec_from_file_location("measure_bundle", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_format_row():
    """One Markdown row: zip size to 1 dp, timing to 2 dp."""
    row = _load_script().format_row("with pyarrow", 41.26, 1.234)
    assert row == "| with pyarrow | 41.3 | 1.23 |"


def test_missing_exe_prints_one_line_and_exits_1(tmp_path, capsys):
    """A missing exe gives one stderr line and exit code 1, not a traceback."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    exe = bundle / "missing.exe"
    code = _load_script().main([str(bundle), str(exe)])
    assert code == 1
    captured = capsys.readouterr()
    assert captured.err == f"measure_bundle: {exe} not found\n"
    assert captured.out == ""
