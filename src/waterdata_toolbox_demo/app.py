"""CLI-first app entrypoint for the Water Data ToolBox packaged app."""

from __future__ import annotations

from collections.abc import Sequence
import sys


def run_cli(argv: Sequence[str]) -> int:
    """Run the command-line interface."""
    from waterdata_toolbox_demo.cli import run_cli as cli_main

    return cli_main(argv)


def run_gui() -> int:
    """Run the desktop GUI."""
    from waterdata_toolbox_demo.gui import run_gui as gui_main

    return gui_main()


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
