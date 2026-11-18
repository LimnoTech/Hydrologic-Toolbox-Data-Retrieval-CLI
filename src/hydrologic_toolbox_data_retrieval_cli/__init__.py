"""Sidecar package for the Hydrologic-Toolbox-DataRetrieval-CLI workflows."""

__all__ = ["__version__"]

try:
    from hydrologic_toolbox_data_retrieval_cli._version import __version__
except ImportError:  # no generated _version.py, e.g. a bare source checkout
    __version__ = "0.0.0"
