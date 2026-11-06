"""CLI-first entrypoint for the Hydrologic-Toolbox-DataRetrieval-CLI app."""

from __future__ import annotations

import sys
from collections.abc import Sequence


def run_cli(argv: Sequence[str]) -> int:
    """Run the command-line interface."""
    from hydrologic_toolbox_data_retrieval_cli.cli import run_cli as cli_main

    return cli_main(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Route the packaged app through the CLI and show help on empty args."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args:
        result = run_cli(args)
    else:
        try:
            result = run_cli(["--help"])
        except SystemExit as exc:
            result = exc.code
    return 0 if result is None else int(result)
