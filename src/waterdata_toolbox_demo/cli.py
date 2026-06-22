"""Command-line interface for the Water Data ToolBox sidecar package."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from waterdata_toolbox_demo.config import DEMO_CONFIG
from waterdata_toolbox_demo.exports import format_artifact_messages
from waterdata_toolbox_demo.station_discovery import run_create_new_project_section
from waterdata_toolbox_demo.timeseries import get_usgs_timeseries
from waterdata_toolbox_demo.xml_compat import handle_xml_request

_WORKFLOW_CHOICES = ("discharge", "gw_daily", "gw_periodic")
_TRUTHY_DEBUG_VALUES = {"1", "true", "yes", "on"}


def _map_workflows(workflow_names):
    """Return the requested workflow names in CLI order."""
    return list(workflow_names)


def _stderr_debug_logger(message):
    """Write one debug message to stderr without touching XML stdout."""
    print(f"[waterdata-toolbox debug] {message}", file=sys.stderr)


def _xml_debug_enabled(args):
    """Return whether XML compatibility debug logging is enabled."""
    env_value = os.environ.get("WATERDATA_TOOLBOX_DEBUG", "")
    return args.debug or env_value.strip().lower() in _TRUTHY_DEBUG_VALUES


def build_parser():
    """Build the top-level CLI parser for the sidecar package."""
    parser = argparse.ArgumentParser(
        prog="waterdata-toolbox-demo",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-new-project")
    create_parser.add_argument(
        "--wf",
        action="append",
        choices=_WORKFLOW_CHOICES,
        required=True,
        help="Workflow to run. Repeat the flag to export more than one workflow.",
    )
    create_parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        required=True,
        help="Bounding box in WEST SOUTH EAST NORTH order.",
    )
    create_parser.add_argument(
        "--output-dir",
        default=DEMO_CONFIG["output_dir"],
        help="Directory where shapefile outputs will be written.",
    )

    add_parser = subparsers.add_parser("add-data")
    add_parser.add_argument(
        "workflow",
        choices=_WORKFLOW_CHOICES,
        help="Workflow to run.",
    )
    add_parser.add_argument(
        "--station-id",
        help="USGS station identifier. Falls back to the demo station for the workflow.",
    )
    add_parser.add_argument(
        "--start-date",
        default=DEMO_CONFIG["date_range"][0],
        help="Start date for the Water Data request in YYYY-MM-DD format.",
    )
    add_parser.add_argument(
        "--end-date",
        default=DEMO_CONFIG["date_range"][1],
        help="End date for the Water Data request in YYYY-MM-DD format.",
    )
    add_parser.add_argument(
        "--output-dir",
        default=DEMO_CONFIG["output_dir"],
        help="Directory where CSV outputs will be written.",
    )

    xml_parser = subparsers.add_parser("xml-compat")
    xml_parser.add_argument(
        "--xml",
        required=True,
        help="HydrologicToolbox NWIS/Water Data XML request string.",
    )
    xml_parser.add_argument(
        "--debug",
        action="store_true",
        help="Write XML compatibility diagnostics to stderr.",
    )

    return parser


def run_cli(argv):
    """Parse CLI arguments, dispatch a workflow, and print concise output."""
    parser = build_parser()
    args = parser.parse_args(list(argv))

    if args.command == "create-new-project":
        workflow_types = _map_workflows(args.wf)
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
        workflow_type = args.workflow
        example = DEMO_CONFIG["example_stations"].get(workflow_type, {})
        station_id = args.station_id or example.get("station_id")
        parameter_code = example.get("parameter_code")
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

    if args.command == "xml-compat":
        if _xml_debug_enabled(args):
            response = handle_xml_request(args.xml, debug_logger=_stderr_debug_logger)
        else:
            response = handle_xml_request(args.xml)
        print(response)
        return 1 if response.startswith("<error>") else 0

    parser.error(f"Unsupported command: {args.command}")
