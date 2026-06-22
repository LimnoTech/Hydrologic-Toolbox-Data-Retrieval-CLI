"""HydrologicToolbox XML compatibility helpers."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from pyproj import CRS, Transformer
from waterdata_toolbox_demo.config import DEMO_CONFIG
from waterdata_toolbox_demo.station_discovery import run_create_new_project_section
from waterdata_toolbox_demo.timeseries import get_usgs_timeseries

_SUPPORTED_DISCOVERY_FUNCTION = "GetNWISStations"
_SUPPORTED_DISCOVERY_DATATYPES = {"discharge", "gw_daily", "gw_periodic"}
_WGS84_CRS = CRS.from_epsg(4326)


def _error_xml(message: str) -> str:
    """Return one XML error payload."""
    return f"<error>{message}</error>"


def _debug(debug_logger, message: str) -> None:
    """Emit one debug message when XML compatibility debugging is enabled."""
    if debug_logger is not None:
        debug_logger(message)


def _parse_xml_root(xml_text: str):
    """Return the parsed XML root or raise a readable validation error."""
    try:
        return ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Invalid XML: {exc}") from exc


def _arguments_element(root):
    """Return the XML arguments element when present."""
    return root.find("arguments")


def _child_text(parent, tag_name: str):
    """Return stripped child text or None when the tag is missing/blank."""
    if parent is None:
        return None
    child = parent.find(tag_name)
    if child is None or child.text is None:
        return None
    text = child.text.strip()
    return text or None


def _required_child_text(parent, tag_name: str):
    """Return stripped child text or raise when the tag is required."""
    value = _child_text(parent, tag_name)
    if value is None:
        raise ValueError(f"Missing required tag: {tag_name}")
    return value


def _repeated_child_text(parent, tag_name: str) -> list[str]:
    """Return non-empty text values for repeated child tags."""
    if parent is None:
        return []

    values = []
    for child in parent.findall(tag_name):
        if child.text is None:
            continue
        text = child.text.strip()
        if text:
            values.append(text)
    return values


def _classify_function(function_name: str | None):
    """Return the XML request kind and workflow, or None when unsupported."""
    if function_name == _SUPPORTED_DISCOVERY_FUNCTION:
        return ("station_discovery", None)
    if not function_name:
        return None

    normalized_name = function_name.lower()
    if "discharge" in normalized_name:
        return ("add_data", "discharge")
    if "periodic" in normalized_name and (
        "groundwater" in normalized_name or normalized_name.endswith("gw")
    ):
        return ("add_data", "gw_periodic")
    if "daily" in normalized_name and (
        "groundwater" in normalized_name or normalized_name.endswith("gw")
    ):
        return ("add_data", "gw_daily")
    return None


def _transform_region_bbox_to_wgs84(region) -> tuple[float, float, float, float]:
    """Return a WGS84 bbox from projected XML region coordinates."""
    north = float(_required_child_text(region, "northbc"))
    south = float(_required_child_text(region, "southbc"))
    east = float(_required_child_text(region, "eastbc"))
    west = float(_required_child_text(region, "westbc"))
    projection = _required_child_text(region, "projection")

    source_crs = CRS.from_user_input(projection)
    transformer = Transformer.from_crs(source_crs, _WGS84_CRS, always_xy=True)

    corners = [
        transformer.transform(west, south),
        transformer.transform(west, north),
        transformer.transform(east, south),
        transformer.transform(east, north),
    ]
    longitudes = [corner[0] for corner in corners]
    latitudes = [corner[1] for corner in corners]
    return (
        min(longitudes),
        min(latitudes),
        max(longitudes),
        max(latitudes),
    )


def _parse_station_discovery_request(function_name: str, arguments):
    """Return one normalized station-discovery request."""
    datatype_values = _repeated_child_text(arguments, "DataType")
    if not datatype_values:
        raise ValueError("Missing required tag: DataType")

    unsupported_datatypes = [
        value for value in datatype_values if value not in _SUPPORTED_DISCOVERY_DATATYPES
    ]
    if unsupported_datatypes:
        raise ValueError(f"Unsupported DataType: {unsupported_datatypes[0]}")

    region = arguments.find("region") if arguments is not None else None
    if region is None:
        raise ValueError("Missing required tag: region")

    return {
        "kind": "station_discovery",
        "function_name": function_name,
        "workflow_types": datatype_values,
        "output_dir": Path(_required_child_text(arguments, "SaveIn")),
        "desired_projection": _child_text(arguments, "DesiredProjection") or "EPSG:4326",
        "bbox": _transform_region_bbox_to_wgs84(region),
        "region_projection": _required_child_text(region, "projection"),
    }


def _parse_add_data_request(function_name: str, workflow_type: str, arguments):
    """Return one normalized add-data request."""
    station_ids = _repeated_child_text(arguments, "stationid")
    if not station_ids:
        raise ValueError("Missing required tag: stationid")

    return {
        "kind": "add_data",
        "function_name": function_name,
        "workflow_type": workflow_type,
        "station_ids": station_ids,
        "output_dir": Path(_required_child_text(arguments, "SaveIn")),
        "desired_projection": _child_text(arguments, "DesiredProjection") or "EPSG:4326",
    }


def parse_xml_request(xml_text: str):
    """Parse one HydrologicToolbox XML request into a normalized mapping."""
    root = _parse_xml_root(xml_text)
    arguments = _arguments_element(root)
    if arguments is None:
        raise ValueError("Missing required tag: arguments")

    _required_child_text(arguments, "SaveIn")
    function_name = root.get("name")
    classification = _classify_function(function_name)
    if classification is None:
        raise ValueError(f"Unsupported function: {function_name}")

    request_kind, workflow_type = classification
    if request_kind == "station_discovery":
        return _parse_station_discovery_request(function_name, arguments)
    if request_kind == "add_data":
        return _parse_add_data_request(function_name, workflow_type, arguments)
    raise ValueError(f"Unsupported function: {function_name}")


def format_station_success_xml(paths_by_workflow: dict[str, Path]) -> str:
    """Return a station-discovery XML success payload."""
    inner = "".join(
        f'<add_shape workflow="{workflow}">{Path(path)}</add_shape>'
        for workflow, path in paths_by_workflow.items()
    )
    return f"<success>{inner}</success>"


def format_add_data_success_xml(result_entries) -> str:
    """Return an add-data XML success payload."""
    inner = "".join(
        f'<add_data type="CSV" subtype="{entry["workflow"]}" stationid="{entry["stationid"]}">{Path(entry["path"])}</add_data>'
        for entry in result_entries
    )
    return f"<success>{inner}</success>"


def handle_xml_request(xml_text: str, debug_logger=None) -> str:
    """Handle one HydrologicToolbox XML request and return XML output."""
    _debug(debug_logger, "xml-compat: received XML request")
    try:
        request = parse_xml_request(xml_text)
    except ValueError as exc:
        _debug(debug_logger, f"xml-compat: validation failed: {exc}")
        return _error_xml(str(exc))

    _debug(
        debug_logger,
        f"xml-compat: parsed function={request['function_name']} kind={request['kind']}",
    )
    if request["kind"] == "station_discovery":
        _debug(
            debug_logger,
            (
                "station-discovery: starting "
                f"workflows={','.join(request['workflow_types'])} "
                f"bbox={request['bbox']} output_dir={request['output_dir']}"
            ),
        )
        results = run_create_new_project_section(
            request["bbox"],
            request["workflow_types"],
            request["output_dir"],
            output_projection=request["desired_projection"],
        )
        for workflow, payload in results.items():
            _debug(
                debug_logger,
                f"station-discovery: workflow={workflow} wrote {payload['files']['shp']}",
            )
        return format_station_success_xml(
            {
                workflow: payload["files"]["shp"]
                for workflow, payload in results.items()
            }
        )
    if request["kind"] == "add_data":
        example = DEMO_CONFIG["example_stations"].get(request["workflow_type"], {})
        result_entries = []
        _debug(
            debug_logger,
            (
                "add-data: starting "
                f"workflow={request['workflow_type']} "
                f"stations={len(request['station_ids'])} "
                f"output_dir={request['output_dir']}"
            ),
        )
        for station_id in request["station_ids"]:
            _debug(debug_logger, f"add-data: station {station_id} download starting")
            download_kwargs = {}
            if debug_logger is not None:
                download_kwargs["debug_logger"] = debug_logger
            payload = get_usgs_timeseries(
                station_id,
                request["workflow_type"],
                request["output_dir"],
                parameter_code=example.get("parameter_code"),
                **download_kwargs,
            )
            _debug(
                debug_logger,
                f"add-data: station {station_id} wrote {payload['files']['csv']}",
            )
            result_entries.append(
                {
                    "workflow": request["workflow_type"],
                    "stationid": station_id,
                    "path": payload["files"]["csv"],
                }
            )
        return format_add_data_success_xml(result_entries)
    return _error_xml(f"Unsupported function: {request['function_name']}")
