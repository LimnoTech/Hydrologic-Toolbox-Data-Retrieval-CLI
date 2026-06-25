"""Command-line interface for the Water Data ToolBox sidecar package."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import traceback

from waterdata_toolbox_demo.config import DEMO_CONFIG
from waterdata_toolbox_demo.exports import format_artifact_messages
from waterdata_toolbox_demo.station_discovery import run_create_new_project_section
from waterdata_toolbox_demo.timeseries import get_usgs_timeseries
from waterdata_toolbox_demo.xml_compat import handle_xml_request

_WORKFLOW_CHOICES = ("discharge", "gw_daily", "gw_periodic")
_TRUTHY_DEBUG_VALUES = {"1", "true", "yes", "on"}
_DEBUG_LOG_ENV_VAR = "WATERDATA_TOOLBOX_DEBUG_LOG"


def _map_workflows(workflow_names):
    """Return the requested workflow names in CLI order."""
    return list(workflow_names)


def _stderr_debug_logger(message):
    """Write one debug message to stderr without touching XML stdout."""
    print(f"[waterdata-toolbox debug] {message}", file=sys.stderr)


def _file_debug_logger(log_path):
    """Return a debug logger that appends messages to a file."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(message):
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        lines = str(message).splitlines() or [""]
        with log_path.open("a", encoding="utf-8") as file_obj:
            for line in lines:
                file_obj.write(f"{timestamp} [waterdata-toolbox debug] {line}\n")

    return log


def _combined_debug_logger(loggers):
    """Return one logger that fans messages out to all active loggers."""
    active_loggers = [logger for logger in loggers if logger is not None]
    if not active_loggers:
        return None

    def log(message):
        for logger in active_loggers:
            logger(message)

    return log


def _xml_debug_enabled(args):
    """Return whether XML compatibility debug logging is enabled."""
    env_value = os.environ.get("WATERDATA_TOOLBOX_DEBUG", "")
    return args.debug or env_value.strip().lower() in _TRUTHY_DEBUG_VALUES


def _xml_debug_log_path(args):
    """Return the configured XML compatibility debug log path, if any."""
    return args.debug_log or os.environ.get(_DEBUG_LOG_ENV_VAR)


def _build_xml_debug_logger(args):
    """Return the configured XML compatibility debug logger, if enabled."""
    file_log_path = _xml_debug_log_path(args)
    return _combined_debug_logger(
        [
            _stderr_debug_logger if _xml_debug_enabled(args) else None,
            _file_debug_logger(file_log_path) if file_log_path else None,
        ]
    )


def _log_process_context(debug_logger, argv):
    """Write process-level context that helps diagnose host-app launch issues."""
    if debug_logger is None:
        return
    debug_logger(f"process: pid={os.getpid()}")
    debug_logger(f"process: cwd={Path.cwd()}")
    debug_logger(f"process: argv={list(argv)}")


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
    xml_parser.add_argument(
        "--debug-log",
        help="Append XML compatibility diagnostics to this log file.",
    )

    return parser


def run_cli(argv):
    """Parse CLI arguments, dispatch a workflow, and print concise output."""
    parser = build_parser()
    argv = list(argv)
    args = parser.parse_args(argv)

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
        debug_logger = _build_xml_debug_logger(args)
        _log_process_context(debug_logger, argv)
        try:
            if debug_logger is not None:
                response = handle_xml_request(args.xml, debug_logger=debug_logger)
            else:
                response = handle_xml_request(args.xml)
        except Exception:
            if debug_logger is not None:
                debug_logger("xml-compat: unhandled exception")
                debug_logger(traceback.format_exc())
            raise
        print(response)
        return 1 if response.startswith("<error>") else 0

    parser.error(f"Unsupported command: {args.command}")
