"""Offline coverage for the HydrologicToolbox XML compatibility layer."""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
from pyproj import CRS, Transformer
import pytest
import shapefile
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def test_parser_accepts_xml_compat_command():
    """The CLI parser should expose the XML compatibility entrypoint."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    args = build_parser().parse_args(["xml-compat", "--xml", "<function />"])

    assert args.command == "xml-compat"
    assert args.xml == "<function />"


def test_parser_accepts_xml_compat_debug_flag():
    """The XML compatibility command should expose optional debug diagnostics."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    args = build_parser().parse_args(
        ["xml-compat", "--debug", "--xml", "<function />"]
    )

    assert args.command == "xml-compat"
    assert args.debug is True


def test_parser_accepts_xml_compat_debug_log_path(tmp_path: Path):
    """The XML compatibility command should support durable debug log files."""
    from hydrologic_toolbox_data_retrieval_cli.cli import build_parser

    log_path = tmp_path / "waterdata-debug.log"

    args = build_parser().parse_args(
        ["xml-compat", "--debug-log", str(log_path), "--xml", "<function />"]
    )

    assert args.command == "xml-compat"
    assert args.debug_log == str(log_path)


def test_xml_request_missing_savein_returns_error_xml():
    """Missing SaveIn should return the approved XML error payload."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import handle_xml_request

    response = handle_xml_request(
        """
        <function name="GetNWISStations">
          <arguments>
            <DataType>discharge</DataType>
            <region>
              <northbc>1</northbc>
              <southbc>0</southbc>
              <eastbc>1</eastbc>
              <westbc>0</westbc>
              <projection>+proj=longlat +datum=WGS84 +no_defs</projection>
            </region>
          </arguments>
        </function>
        """
    )

    assert response == "<error>Missing required tag: SaveIn</error>"


def test_xml_request_invalid_xml_returns_error_xml():
    """Malformed XML should return a stable XML error payload."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import handle_xml_request

    response = handle_xml_request("<function")

    assert response.startswith("<error>Invalid XML:")


def test_station_request_missing_datatype_returns_error_xml():
    """Station discovery XML should require at least one DataType tag."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import handle_xml_request

    response = handle_xml_request(
        """
        <function name="GetNWISStations">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <region>
              <northbc>1</northbc>
              <southbc>0</southbc>
              <eastbc>1</eastbc>
              <westbc>0</westbc>
              <projection>+proj=longlat +datum=WGS84 +no_defs</projection>
            </region>
          </arguments>
        </function>
        """
    )

    assert response == "<error>Missing required tag: DataType</error>"


def test_station_request_missing_region_projection_returns_error_xml():
    """Station discovery XML should require a region projection string."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import handle_xml_request

    response = handle_xml_request(
        """
        <function name="GetNWISStations">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <DataType>discharge</DataType>
            <region>
              <northbc>1</northbc>
              <southbc>0</southbc>
              <eastbc>1</eastbc>
              <westbc>0</westbc>
            </region>
          </arguments>
        </function>
        """
    )

    assert response == "<error>Missing required tag: projection</error>"


def test_add_data_request_missing_stationid_returns_error_xml():
    """Add-data XML should require at least one stationid tag."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import handle_xml_request

    response = handle_xml_request(
        """
        <function name="GetNWISDailyDischarge">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
          </arguments>
        </function>
        """
    )

    assert response == "<error>Missing required tag: stationid</error>"


def test_unsupported_function_returns_error_xml():
    """Unknown XML function names should fail cleanly."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import handle_xml_request

    response = handle_xml_request(
        """
        <function name="GetSomethingElse">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
          </arguments>
        </function>
        """
    )

    assert response == "<error>Unsupported function: GetSomethingElse</error>"


def test_parse_station_request_defaults_desired_projection_to_wgs84():
    """Station requests should default DesiredProjection to WGS84."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import parse_xml_request

    request = parse_xml_request(
        """
        <function name="GetNWISStations">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <DataType>discharge</DataType>
            <region>
              <northbc>1</northbc>
              <southbc>0</southbc>
              <eastbc>1</eastbc>
              <westbc>0</westbc>
              <projection>+proj=longlat +datum=WGS84 +no_defs</projection>
            </region>
          </arguments>
        </function>
        """
    )

    assert request["desired_projection"] == "EPSG:4326"


def test_parse_station_request_transforms_region_bbox_to_wgs84():
    """Station requests should transform projected region bounds into WGS84."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import parse_xml_request

    west, south, east, north = (-82.859, 31.899, -82.013, 32.947)
    source_projection = "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs"
    transformer = Transformer.from_crs(CRS.from_epsg(4326), CRS.from_proj4(source_projection), always_xy=True)
    west_x, south_y = transformer.transform(west, south)
    east_x, north_y = transformer.transform(east, north)

    request = parse_xml_request(
        f"""
        <function name="GetNWISStations">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <DataType>discharge</DataType>
            <region>
              <northbc>{north_y}</northbc>
              <southbc>{south_y}</southbc>
              <eastbc>{east_x}</eastbc>
              <westbc>{west_x}</westbc>
              <projection>{source_projection}</projection>
            </region>
          </arguments>
        </function>
        """
    )

    transformed = request["bbox"]
    assert transformed[0] == pytest.approx(west, abs=0.01)
    assert transformed[1] == pytest.approx(south, abs=0.01)
    assert transformed[2] == pytest.approx(east, abs=0.01)
    assert transformed[3] == pytest.approx(north, abs=0.01)


def test_parse_add_data_request_keeps_multiple_station_ids():
    """Add-data XML should preserve multiple station IDs in request order."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import parse_xml_request

    request = parse_xml_request(
        """
        <function name="GetNWISDailyDischarge">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>02336106</stationid>
            <stationid>02336107</stationid>
          </arguments>
        </function>
        """
    )

    assert request["kind"] == "add_data"
    assert request["workflow_type"] == "discharge"
    assert request["station_ids"] == ["02336106", "02336107"]


def test_format_station_success_xml_lists_output_paths():
    """Station XML success payload should enumerate shapefile paths."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import format_station_success_xml

    response = format_station_success_xml(
        {
            "discharge": Path("/tmp/NWIS_Stations_discharge.shp"),
            "gw_daily": Path("/tmp/NWIS_Stations_gw_daily.shp"),
        }
    )

    assert response == (
        "<success>"
        '<add_shape workflow="discharge">/tmp/NWIS_Stations_discharge.shp</add_shape>'
        '<add_shape workflow="gw_daily">/tmp/NWIS_Stations_gw_daily.shp</add_shape>'
        "</success>"
    )


def test_format_add_data_success_xml_lists_output_paths():
    """Add-data XML success payload should enumerate CSV paths."""
    from hydrologic_toolbox_data_retrieval_cli.xml_compat import format_add_data_success_xml

    response = format_add_data_success_xml(
        [
            {
                "workflow": "discharge",
                "stationid": "02336106",
                "path": Path("/tmp/discharge_02336106.csv"),
            },
            {
                "workflow": "gw_daily",
                "stationid": "324209082430201",
                "path": Path("/tmp/gw_daily_324209082430201.csv"),
            },
        ]
    )

    assert response == (
        "<success>"
        '<add_data type="CSV" subtype="discharge" stationid="02336106">/tmp/discharge_02336106.csv</add_data>'
        '<add_data type="CSV" subtype="gw_daily" stationid="324209082430201">/tmp/gw_daily_324209082430201.csv</add_data>'
        "</success>"
    )


def test_projection_aware_station_export_reprojects_output(tmp_path: Path):
    """Station shapefile export should honor an explicit output projection."""
    from hydrologic_toolbox_data_retrieval_cli.exports import export_station_shapefile_artifacts

    frame = gpd.GeoDataFrame(
        {
            "monitoring_location_id": ["USGS-123"],
            "monitoring_location_number": ["123"],
            "monitoring_location_name": ["Example station"],
            "site_type_code": ["ST"],
        },
        geometry=[Point(-82.5, 32.5)],
        crs="EPSG:4326",
    )

    output = export_station_shapefile_artifacts(
        frame,
        tmp_path,
        "stations",
        output_projection="+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs",
    )

    prj_text = output["shp"].with_suffix(".prj").read_text(encoding="utf-8")
    shape = shapefile.Reader(str(output["shp"])).shape(0)

    assert "Mercator" in prj_text or "merc" in prj_text.lower()
    assert shape.points[0][0] != pytest.approx(-82.5)
    assert shape.points[0][1] != pytest.approx(32.5)


def test_handle_xml_request_station_discovery_returns_success_xml(monkeypatch, tmp_path: Path):
    """Station-discovery XML requests should return add_shape success XML."""
    from hydrologic_toolbox_data_retrieval_cli import xml_compat

    expected_shp = tmp_path / "NWIS_Stations_discharge.shp"

    def fake_run_create_new_project_section(
        bbox,
        workflow_types,
        output_dir,
        waterdata_module=None,
        output_projection=None,
    ):
        assert workflow_types == ["discharge"]
        assert output_dir == Path("/tmp/out")
        assert output_projection == "EPSG:4326"
        assert len(bbox) == 4
        return {
            "discharge": {
                "files": {"shp": expected_shp},
            }
        }

    monkeypatch.setattr(
        xml_compat,
        "run_create_new_project_section",
        fake_run_create_new_project_section,
    )

    response = xml_compat.handle_xml_request(
        """
        <function name="GetNWISStations">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <DataType>discharge</DataType>
            <region>
              <northbc>1</northbc>
              <southbc>0</southbc>
              <eastbc>1</eastbc>
              <westbc>0</westbc>
              <projection>+proj=longlat +datum=WGS84 +no_defs</projection>
            </region>
          </arguments>
        </function>
        """
    )

    assert response == (
        "<success>"
        f'<add_shape workflow="discharge">{expected_shp}</add_shape>'
        "</success>"
    )


def test_handle_xml_request_add_data_returns_success_xml(monkeypatch, tmp_path: Path):
    """Add-data XML requests should return add_data success XML per station."""
    from hydrologic_toolbox_data_retrieval_cli import xml_compat

    expected_a = tmp_path / "discharge_02336106.csv"
    expected_b = tmp_path / "discharge_02336107.csv"

    def fake_get_usgs_timeseries(
        station_id,
        workflow_type,
        output_dir,
        parameter_code=None,
        date_range=("1880-01-01", "2100-01-01"),
        waterdata_module=None,
    ):
        return {
            "files": {"csv": expected_a if station_id == "02336106" else expected_b},
            "frame": [],
        }

    monkeypatch.setattr(xml_compat, "get_usgs_timeseries", fake_get_usgs_timeseries)

    response = xml_compat.handle_xml_request(
        """
        <function name="GetNWISDailyDischarge">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>02336106</stationid>
            <stationid>02336107</stationid>
          </arguments>
        </function>
        """
    )

    assert response == (
        "<success>"
        f'<add_data type="CSV" subtype="discharge" stationid="02336106">{expected_a}</add_data>'
        f'<add_data type="CSV" subtype="discharge" stationid="02336107">{expected_b}</add_data>'
        "</success>"
    )


def test_handle_xml_request_bundle_uses_valid_add_data_function(monkeypatch, tmp_path: Path):
    """HydrologicToolbox can send multiple function blocks in one XML argument."""
    from hydrologic_toolbox_data_retrieval_cli import xml_compat

    expected_csv = tmp_path / "discharge_02357150.csv"
    messages = []

    def fake_get_usgs_timeseries(
        station_id,
        workflow_type,
        output_dir,
        parameter_code=None,
        date_range=("1880-01-01", "2100-01-01"),
        waterdata_module=None,
        debug_logger=None,
    ):
        assert station_id == "02357150"
        assert workflow_type == "discharge"
        assert output_dir == Path("/tmp/out")
        return {
            "files": {"csv": expected_csv},
            "frame": [1, 2, 3],
        }

    monkeypatch.setattr(xml_compat, "get_usgs_timeseries", fake_get_usgs_timeseries)

    response = xml_compat.handle_xml_request(
        """
        <function name="GetNWISStations">
          <arguments>
            <DataType>discharge</DataType>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>02357150</stationid>
          </arguments>
        </function>

        <function name="GetNWISDailyDischarge">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>02357150</stationid>
          </arguments>
        </function>
        """,
        debug_logger=messages.append,
    )

    assert response == (
        "<success>"
        f'<add_data type="CSV" subtype="discharge" stationid="02357150">{expected_csv}</add_data>'
        "</success>"
    )
    assert "xml-compat: found 2 function blocks" in messages
    assert "xml-compat: parsed 1 function blocks" in messages
    assert any(
        "xml-compat: skipping function=GetNWISStations" in message
        for message in messages
    )


def test_handle_xml_request_bundle_combines_add_data_results(monkeypatch, tmp_path: Path):
    """Multiple valid add-data function blocks should return one combined success XML."""
    from hydrologic_toolbox_data_retrieval_cli import xml_compat

    expected_discharge = tmp_path / "discharge_02357150.csv"
    expected_daily = tmp_path / "gw_daily_324209082430201.csv"
    calls = []

    def fake_get_usgs_timeseries(
        station_id,
        workflow_type,
        output_dir,
        parameter_code=None,
        date_range=("1880-01-01", "2100-01-01"),
        waterdata_module=None,
        debug_logger=None,
    ):
        calls.append((station_id, workflow_type, parameter_code))
        path = expected_daily if workflow_type == "gw_daily" else expected_discharge
        return {
            "files": {"csv": path},
            "frame": [1],
        }

    monkeypatch.setattr(xml_compat, "get_usgs_timeseries", fake_get_usgs_timeseries)

    response = xml_compat.handle_xml_request(
        """
        <function name="GetNWISDailyDischarge">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>02357150</stationid>
          </arguments>
        </function>
        <function name="GetNWISDailyGroundwater">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>324209082430201</stationid>
          </arguments>
        </function>
        """
    )

    assert calls == [
        ("02357150", "discharge", "00060"),
        ("324209082430201", "gw_daily", "72019"),
    ]
    assert response == (
        "<success>"
        f'<add_data type="CSV" subtype="discharge" stationid="02357150">{expected_discharge}</add_data>'
        f'<add_data type="CSV" subtype="gw_daily" stationid="324209082430201">{expected_daily}</add_data>'
        "</success>"
    )


def test_handle_xml_request_add_data_emits_debug_messages(monkeypatch, tmp_path: Path):
    """Debug mode should report XML and add-data milestones without changing XML."""
    from hydrologic_toolbox_data_retrieval_cli import xml_compat

    expected_csv = tmp_path / "discharge_02336106.csv"
    messages = []

    def fake_get_usgs_timeseries(
        station_id,
        workflow_type,
        output_dir,
        parameter_code=None,
        date_range=("1880-01-01", "2100-01-01"),
        waterdata_module=None,
        debug_logger=None,
    ):
        assert debug_logger is not None
        debug_logger(f"fake download reached for {station_id}")
        return {
            "files": {"csv": expected_csv},
            "frame": [1, 2, 3],
        }

    monkeypatch.setattr(xml_compat, "get_usgs_timeseries", fake_get_usgs_timeseries)

    response = xml_compat.handle_xml_request(
        """
        <function name="GetNWISDailyDischarge">
          <arguments>
            <SaveIn>/tmp/out</SaveIn>
            <stationid>02336106</stationid>
          </arguments>
        </function>
        """,
        debug_logger=messages.append,
    )

    assert response == (
        "<success>"
        f'<add_data type="CSV" subtype="discharge" stationid="02336106">{expected_csv}</add_data>'
        "</success>"
    )
    assert "xml-compat: received XML request" in messages
    assert "xml-compat: parsed function=GetNWISDailyDischarge kind=add_data" in messages
    assert "add-data: starting workflow=discharge stations=1 output_dir=/tmp/out" in messages
    assert "add-data: station 02336106 download starting" in messages
    assert "fake download reached for 02336106" in messages
    assert f"add-data: station 02336106 wrote {expected_csv}" in messages


def test_run_cli_xml_compat_success_prints_xml(monkeypatch, capsys):
    """The CLI should print XML success payloads unchanged."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    monkeypatch.setattr(cli, "handle_xml_request", lambda xml_text: "<success />")

    result = cli.run_cli(["xml-compat", "--xml", "<function />"])
    output = capsys.readouterr().out.strip()

    assert result == 0
    assert output == "<success />"


def test_run_cli_xml_compat_debug_prints_diagnostics_to_stderr(monkeypatch, capsys):
    """Debug messages should not pollute stdout XML consumed by HydrologicToolbox."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    def fake_handle_xml_request(xml_text, debug_logger=None):
        assert xml_text == "<function />"
        assert debug_logger is not None
        debug_logger("xml parser reached")
        return "<success />"

    monkeypatch.setattr(cli, "handle_xml_request", fake_handle_xml_request)

    result = cli.run_cli(["xml-compat", "--debug", "--xml", "<function />"])
    captured = capsys.readouterr()

    assert result == 0
    assert captured.out.strip() == "<success />"
    assert "[htdr-cli debug] xml parser reached" in captured.err


def test_run_cli_xml_compat_debug_can_be_enabled_by_environment(monkeypatch, capsys):
    """Debug logging should be available even when callers cannot add CLI flags."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    def fake_handle_xml_request(xml_text, debug_logger=None):
        assert debug_logger is not None
        debug_logger("environment debug reached")
        return "<success />"

    monkeypatch.setenv("HYDROLOGIC_TOOLBOX_DEBUG", "1")
    monkeypatch.setattr(cli, "handle_xml_request", fake_handle_xml_request)

    result = cli.run_cli(["xml-compat", "--xml", "<function />"])
    captured = capsys.readouterr()

    assert result == 0
    assert captured.out.strip() == "<success />"
    assert "[htdr-cli debug] environment debug reached" in captured.err


def test_run_cli_xml_compat_writes_debug_log_file(monkeypatch, capsys, tmp_path: Path):
    """File logging should provide diagnostics without relying on console output."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    log_path = tmp_path / "waterdata-debug.log"

    def fake_handle_xml_request(xml_text, debug_logger=None):
        assert debug_logger is not None
        debug_logger("file debug reached")
        return "<success />"

    monkeypatch.setattr(cli, "handle_xml_request", fake_handle_xml_request)

    result = cli.run_cli(
        [
            "xml-compat",
            "--debug-log",
            str(log_path),
            "--xml",
            "<function />",
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert captured.out.strip() == "<success />"
    assert captured.err == ""
    log_text = log_path.read_text(encoding="utf-8")
    assert "[htdr-cli debug] process: pid=" in log_text
    assert "[htdr-cli debug] process: cwd=" in log_text
    assert "[htdr-cli debug] file debug reached" in log_text


def test_run_cli_xml_compat_debug_log_can_be_enabled_by_environment(
    monkeypatch,
    capsys,
    tmp_path: Path,
):
    """Calling apps should be able to request file logs without changing args."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    log_path = tmp_path / "waterdata-debug.log"

    def fake_handle_xml_request(xml_text, debug_logger=None):
        assert debug_logger is not None
        debug_logger("environment file debug reached")
        return "<success />"

    monkeypatch.setenv("HYDROLOGIC_TOOLBOX_DEBUG_LOG", str(log_path))
    monkeypatch.setattr(cli, "handle_xml_request", fake_handle_xml_request)

    result = cli.run_cli(["xml-compat", "--xml", "<function />"])
    captured = capsys.readouterr()

    assert result == 0
    assert captured.out.strip() == "<success />"
    assert "[htdr-cli debug] environment file debug reached" in log_path.read_text(
        encoding="utf-8"
    )


def test_run_cli_xml_compat_debug_log_records_unhandled_exception(
    monkeypatch,
    tmp_path: Path,
):
    """Unexpected failures should leave a traceback in the debug log."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    log_path = tmp_path / "waterdata-debug.log"

    def fake_handle_xml_request(xml_text, debug_logger=None):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(cli, "handle_xml_request", fake_handle_xml_request)

    with pytest.raises(RuntimeError):
        cli.run_cli(
            [
                "xml-compat",
                "--debug-log",
                str(log_path),
                "--xml",
                "<function />",
            ]
        )

    log_text = log_path.read_text(encoding="utf-8")
    assert "[htdr-cli debug] xml-compat: unhandled exception" in log_text
    assert "RuntimeError: simulated failure" in log_text


def test_run_cli_xml_compat_error_returns_nonzero(monkeypatch, capsys):
    """The CLI should print XML errors and return a nonzero exit code."""
    from hydrologic_toolbox_data_retrieval_cli import cli

    monkeypatch.setattr(cli, "handle_xml_request", lambda xml_text: "<error>bad request</error>")

    result = cli.run_cli(["xml-compat", "--xml", "<function />"])
    output = capsys.readouterr().out.strip()

    assert result == 1
    assert output == "<error>bad request</error>"
