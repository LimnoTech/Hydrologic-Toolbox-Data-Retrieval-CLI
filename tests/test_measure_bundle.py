"""The pure parts of ``scripts/measure_bundle.py``."""

from __future__ import annotations

import importlib.util
import os
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


def _failing_exe(directory: Path, code: int) -> Path:
    """Return a tiny executable that exits with ``code``, on any OS."""
    if os.name == "nt":
        exe = directory / "fails.cmd"
        exe.write_text(f"@echo off\r\nexit /b {code}\r\n")
    else:
        exe = directory / "fails.sh"
        exe.write_text(f"#!/bin/sh\nexit {code}\n")
        exe.chmod(0o755)
    return exe


def test_help_failure_prints_one_line_exits_1_and_leaves_no_zip(tmp_path, capsys):
    """A ``--help`` that exits non-zero gives one stderr line, exit 1, no zip."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    exe = _failing_exe(bundle, 3)
    code = _load_script().main([str(bundle), str(exe)])
    assert code == 1
    captured = capsys.readouterr()
    assert captured.err == f"measure_bundle: {exe} --help exited 3\n"
    assert captured.out == ""
    assert not (tmp_path / "bundle.zip").exists()


def test_missing_exe_leaves_no_zip(tmp_path):
    """The exe is checked before zipping, so a missing exe leaves no stray zip."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    assert _load_script().main([str(bundle), str(bundle / "missing.exe")]) == 1
    assert not (tmp_path / "bundle.zip").exists()


def test_missing_bundle_dir_prints_one_line_and_exits_1(tmp_path, capsys):
    """A missing bundle directory gives one stderr line and exit 1, no traceback."""
    bundle = tmp_path / "no_such_bundle"
    code = _load_script().main([str(bundle), str(bundle / "app.exe")])
    assert code == 1
    captured = capsys.readouterr()
    assert captured.err == f"measure_bundle: bundle directory {bundle} not found\n"
    assert captured.out == ""


def _bundle_with_payload(tmp_path: Path, payload_bytes: int) -> tuple[Path, Path]:
    """Return a bundle dir and a working exe, plus an incompressible payload."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    exe = _failing_exe(bundle, 0)
    (bundle / "payload.bin").write_bytes(os.urandom(payload_bytes))
    return bundle, exe


def test_under_the_limit_prints_row_and_exits_0(tmp_path, capsys):
    """A zip under ``--max-mb`` prints its row, nothing on stderr, and exits 0."""
    bundle, exe = _bundle_with_payload(tmp_path, 200_000)
    code = _load_script().main(
        [str(bundle), str(exe), "--label", "lean", "--max-mb", "250"]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("| lean | 0.2 | ")
    assert captured.err == ""


def test_over_the_limit_prints_row_then_one_line_and_exits_1(tmp_path, capsys):
    """A zip over ``--max-mb`` still prints its row, then one stderr line, exit 1."""
    bundle, exe = _bundle_with_payload(tmp_path, 200_000)
    code = _load_script().main(
        [str(bundle), str(exe), "--label", "fat", "--max-mb", "0.1"]
    )
    assert code == 1
    captured = capsys.readouterr()
    assert captured.out.startswith("| fat | 0.2 | ")
    assert captured.err == "bundle zip is 0.20 MB, over the 0.1 MB limit\n"


def test_exactly_at_the_limit_passes(tmp_path, capsys):
    """The check is strict ``>``: a zip exactly at ``--max-mb`` exits 0, no stderr."""
    bundle, exe = _bundle_with_payload(tmp_path, 200_000)
    script = _load_script()
    assert script.main([str(bundle), str(exe)]) == 0
    capsys.readouterr()
    limit = (tmp_path / "bundle.zip").stat().st_size / 1_000_000
    code = script.main([str(bundle), str(exe), "--max-mb", repr(limit)])
    assert code == 0
    assert capsys.readouterr().err == ""
