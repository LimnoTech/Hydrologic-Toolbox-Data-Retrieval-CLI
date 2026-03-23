"""Command-line interface for the Water Data ToolBox sidecar package."""

from __future__ import annotations

import argparse
from pathlib import Path

from waterdata_toolbox_demo.config import DEMO_CONFIG
from waterdata_toolbox_demo.exports import format_artifact_messages
from waterdata_toolbox_demo.station_discovery import get_usgs_stations_in_bbox
from waterdata_toolbox_demo.timeseries import get_usgs_timeseries


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
    create_parser.add_argument(
        "--workflow-type",
        dest="workflow_types",
        action="append",
        choices=["discharge", "gw_daily", "gw_periodic"],
        default=None,
    )

    add_parser = subparsers.add_parser("add-data")
    add_parser.add_argument(
        "--workflow-type",
        choices=["discharge", "gw_daily", "gw_periodic"],
        required=True,
    )
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
        workflow_types = args.workflow_types or list(DEMO_CONFIG["example_stations"].keys())
        results = get_usgs_stations_in_bbox(tuple(args.bbox), workflow_types)
        for workflow_type in workflow_types:
            frame = results[workflow_type]
            print(f"{workflow_type}: {len(frame)} stations")
        return 0

    if args.command == "add-data":
        example = DEMO_CONFIG["example_stations"].get(args.workflow_type, {})
        station_id = args.station_id or example.get("station_id")
        parameter_code = args.parameter_code or example.get("parameter_code")
        payload = get_usgs_timeseries(
            station_id,
            args.workflow_type,
            Path(args.output_dir),
            parameter_code=parameter_code,
            date_range=(args.start_date, args.end_date),
        )
        print(f"{args.workflow_type}: {len(payload['frame'])} rows")
        for message in format_artifact_messages(payload["files"]):
            print(message)
        return 0

    parser.error(f"Unsupported command: {args.command}")
