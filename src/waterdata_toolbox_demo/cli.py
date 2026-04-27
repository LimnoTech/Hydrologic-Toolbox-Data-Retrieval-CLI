"""Command-line interface for the Water Data ToolBox sidecar package."""

from __future__ import annotations

import argparse
from pathlib import Path

from waterdata_toolbox_demo.config import DEMO_CONFIG
from waterdata_toolbox_demo.exports import format_artifact_messages
from waterdata_toolbox_demo.station_discovery import run_create_new_project_section
from waterdata_toolbox_demo.timeseries import get_usgs_timeseries

_WORKFLOW_FLAG_MAP = (
    ("discharge", "discharge"),
    ("daily", "gw_daily"),
    ("periodic", "gw_periodic"),
)


def _add_workflow_flags(parser):
    """Add the shared human-facing workflow flags to a parser."""
    parser.add_argument("--discharge", action="store_true")
    parser.add_argument("--daily", action="store_true")
    parser.add_argument("--periodic", action="store_true")


def _selected_workflows(args):
    """Return the internal workflow ids selected by the human-facing flags."""
    selected = []
    for attribute_name, workflow_type in _WORKFLOW_FLAG_MAP:
        if getattr(args, attribute_name, False):
            selected.append(workflow_type)
    return selected


def build_parser():
    """Build the top-level CLI parser for the sidecar package."""
    parser = argparse.ArgumentParser(prog="waterdata-toolbox-demo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-new-project")
    create_parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        default=DEMO_CONFIG["bbox"],
    )
    create_parser.add_argument("--output-dir", default=DEMO_CONFIG["output_dir"])
    _add_workflow_flags(create_parser)

    add_parser = subparsers.add_parser("add-data")
    _add_workflow_flags(add_parser)
    add_parser.add_argument("--station-id")
    add_parser.add_argument("--parameter-code")
    add_parser.add_argument("--start-date", default=DEMO_CONFIG["date_range"][0])
    add_parser.add_argument("--end-date", default=DEMO_CONFIG["date_range"][1])
    add_parser.add_argument("--output-dir", default=DEMO_CONFIG["output_dir"])

    return parser


def run_cli(argv):
    """Parse CLI arguments, dispatch a workflow, and print concise output."""
    parser = build_parser()
    args = parser.parse_args(list(argv))

    if args.command == "create-new-project":
        workflow_types = _selected_workflows(args)
        if not workflow_types:
            parser.error(
                "create-new-project requires at least one of --discharge, --daily, or --periodic"
            )
        results = run_create_new_project_section(
            tuple(args.bbox),
            workflow_types,
            Path(args.output_dir),
        )
        for workflow_type in workflow_types:
            frame = results[workflow_type]["frame"]
            print(f"{workflow_type}: {len(frame)} stations")
            for message in results[workflow_type]["artifact_messages"]:
                print(message)
        return 0

    if args.command == "add-data":
        workflow_types = _selected_workflows(args)
        if len(workflow_types) != 1:
            parser.error("add-data requires exactly one of --discharge, --daily, or --periodic")

        workflow_type = workflow_types[0]
        example = DEMO_CONFIG["example_stations"].get(workflow_type, {})
        station_id = args.station_id or example.get("station_id")
        parameter_code = args.parameter_code or example.get("parameter_code")
        payload = get_usgs_timeseries(
            station_id,
            workflow_type,
            Path(args.output_dir),
            parameter_code=parameter_code,
            date_range=(args.start_date, args.end_date),
        )
        print(f"{workflow_type}: {len(payload['frame'])} rows")
        for message in format_artifact_messages(payload["files"]):
            print(message)
        return 0

    parser.error(f"Unsupported command: {args.command}")
