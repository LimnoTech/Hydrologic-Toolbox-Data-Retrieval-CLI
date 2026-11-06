"""``__version__`` and the top-level ``--version`` flag."""

from __future__ import annotations

import importlib
import subprocess
import sys

import pytest

import hydrologic_toolbox_data_retrieval_cli as package


def test_version_flag_prints_package_version():
    """``--version`` prints exactly the package version and a newline."""
    result = subprocess.run(
        [sys.executable, "-m", "hydrologic_toolbox_data_retrieval_cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{package.__version__}\n"


@pytest.fixture
def package_without_version_module(monkeypatch):
    """Reload the package as if the generated ``_version`` module were missing.

    The ``sys.modules`` patch lives in a ``monkeypatch.context()`` that has exited
    before the final reload runs, so the package is always rebuilt from the real
    ``_version`` module, and a failing reload cannot hide a test's assertion.
    """
    try:
        with monkeypatch.context() as patch:
            # A None entry in sys.modules makes `import ..._version` raise ImportError.
            patch.setitem(
                sys.modules, "hydrologic_toolbox_data_retrieval_cli._version", None
            )
            yield importlib.reload(package)
    finally:
        importlib.reload(package)


def test_version_falls_back_without_version_module(package_without_version_module):
    """Without a generated ``_version`` module the version is ``0.0.0``."""
    assert package_without_version_module.__version__ == "0.0.0"
