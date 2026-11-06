"""``__version__`` and the top-level ``--version`` flag."""

from __future__ import annotations

import importlib
import subprocess
import sys

import hydrologic_toolbox_data_retrieval_cli as package


def test_version_flag_prints_package_version():
    result = subprocess.run(
        [sys.executable, "-m", "hydrologic_toolbox_data_retrieval_cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{package.__version__}\n"


def test_version_falls_back_without_version_module(monkeypatch):
    # A None entry in sys.modules makes `import ..._version` raise ImportError.
    monkeypatch.setitem(sys.modules, "hydrologic_toolbox_data_retrieval_cli._version", None)
    try:
        reloaded = importlib.reload(package)
        assert reloaded.__version__ == "0.0.0"
    finally:
        monkeypatch.undo()
        importlib.reload(package)
