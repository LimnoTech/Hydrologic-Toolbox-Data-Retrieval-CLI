"""HydrologicToolbox XML compatibility helpers."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from pyproj import CRS, Transformer
from hydrologic_toolbox_data_retrieval_cli.config import DEMO_CONFIG
from hydrologic_toolbox_data_retrieval_cli.station_discovery import run_create_new_project_section
from hydrologic_toolbox_data_retrieval_cli.timeseries import get_usgs_timeseries

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


def _parse_xml_function_roots(xml_text: str):
    """Return one or more top-level function elements from XML text."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as original_exc:
        try:
            root = ElementTree.fromstring(f"<xml_compat_bundle>{xml_text}</xml_compat_bundle>")
        except ElementTree.ParseError:
            raise ValueError(f"Invalid XML: {original_exc}") from original_exc

    if root.tag == "function":
        return [root]

    function_roots = [child for child in list(root) if child.tag == "function"]
    if function_roots:
        return function_roots

    return [root]


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
    root = _parse_xml_function_roots(xml_text)[0]
    return _parse_xml_request_root(root)


def _parse_xml_request_root(root):
    """Parse one XML function root into a normalized mapping."""
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


def parse_xml_requests(xml_text: str):
    """Parse one or more HydrologicToolbox XML function blocks."""
    return [_parse_xml_request_root(root) for root in _parse_xml_function_roots(xml_text)]


def _parse_xml_requests_with_skips(xml_text: str, debug_logger=None):
    """Parse XML functions, skipping invalid entries only in bundled XML."""
    function_roots = _parse_xml_function_roots(xml_text)
    _debug(debug_logger, f"xml-compat: found {len(function_roots)} function blocks")
    requests = []
    errors = []
    for root in function_roots:
        function_name = root.get("name")
        try:
            requests.append(_parse_xml_request_root(root))
        except ValueError as exc:
            errors.append(exc)
            if len(function_roots) > 1:
                _debug(
                    debug_logger,
                    f"xml-compat: skipping function={function_name}: {exc}",
                )
                continue
            raise

    if not requests and errors:
        raise errors[0]
    return requests


def format_station_success_xml(paths_by_workflow: dict[str, Path]) -> str:
    """Return a station-discovery XML success payload."""
    inner = "".join(format_station_success_entries(paths_by_workflow))
    return f"<success>{inner}</success>"


def format_station_success_entries(paths_by_workflow: dict[str, Path]) -> list[str]:
    """Return station-discovery XML success elements."""
    return [
        f'<add_shape workflow="{workflow}">{Path(path)}</add_shape>'
        for workflow, path in paths_by_workflow.items()
    ]


def format_add_data_success_xml(result_entries) -> str:
    """Return an add-data XML success payload."""
    inner = "".join(format_add_data_success_entries(result_entries))
    return f"<success>{inner}</success>"


def format_add_data_success_entries(result_entries) -> list[str]:
    """Return add-data XML success elements."""
    return [
        f'<add_data type="CSV" subtype="{entry["workflow"]}" stationid="{entry["stationid"]}">{Path(entry["path"])}</add_data>'
        for entry in result_entries
    ]


def handle_xml_request(xml_text: str, debug_logger=None) -> str:
    """Handle one HydrologicToolbox XML request and return XML output."""
    _debug(debug_logger, "xml-compat: received XML request")
    try:
        requests = _parse_xml_requests_with_skips(xml_text, debug_logger=debug_logger)
    except ValueError as exc:
        _debug(debug_logger, f"xml-compat: validation failed: {exc}")
        return _error_xml(str(exc))

    _debug(debug_logger, f"xml-compat: parsed {len(requests)} function blocks")
    success_entries = []
    for request in requests:
        _debug(
            debug_logger,
            f"xml-compat: parsed function={request['function_name']} kind={request['kind']}",
        )
        success_entries.extend(_handle_xml_request_mapping(request, debug_logger))
    if success_entries:
        return f"<success>{''.join(success_entries)}</success>"
    return _error_xml("No supported XML functions found")


def _handle_xml_request_mapping(request, debug_logger=None) -> list[str]:
    """Handle one parsed XML request and return success XML elements."""
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
        return format_station_success_entries(
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
        return format_add_data_success_entries(result_entries)
    raise ValueError(f"Unsupported function: {request['function_name']}")
