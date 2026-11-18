"""Sidecar package for the hydrotoolbox-dataretrieval workflows."""

__all__ = ["__version__"]

try:
    from hydrotoolbox_dataretrieval._version import __version__
except ImportError:  # no generated _version.py, e.g. a bare source checkout
    __version__ = "0.0.0"
