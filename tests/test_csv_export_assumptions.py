"""Small CSV export assumptions that guide Hydrologic Toolbox fixes."""

from __future__ import annotations

import pandas as pd


def _read_lines(path):
    return path.read_text(encoding="utf-8").splitlines()


def test_categorical_dtype_does_not_force_csv_quotes():
    """Categorical dtype preserves text values but does not control CSV quoting."""
    category_dtype = pd.CategoricalDtype()
    frame = pd.DataFrame(
        {
            "site_no": pd.Series(["04193500"], dtype=category_dtype),
            "Station name": pd.Series(
                ["MAUMEE RIVER AT WATERVILLE OH"],
                dtype=category_dtype,
            ),
            "HUC code": pd.Series(["04100009"], dtype=category_dtype),
        }
    )

    lines = frame.to_csv(index=False).splitlines()

    assert lines[1] == "04193500,MAUMEE RIVER AT WATERVILLE OH,04100009"
    assert '"' not in lines[1]


def test_forced_quote_fields_are_the_csv_quoting_control():
    """Our exporter's forced-quote policy is what makes identifiers explicit text."""
    from hydrologic_toolbox_data_retrieval_cli.exports import _format_csv_line

    fields = ["site_no", "Station name", "HUC code"]
    values = ["04193500", "MAUMEE RIVER AT WATERVILLE OH", "04100009"]

    line = _format_csv_line(
        values,
        forced_quote_fields=set(fields),
        field_names=fields,
    )

    assert line == '"04193500","MAUMEE RIVER AT WATERVILLE OH","04100009"'


def test_reduced_header_quotes_text_identifier_fields(tmp_path):
    """Discharge/daily metadata should quote fields Hydrologic Toolbox reads as text."""
    from hydrologic_toolbox_data_retrieval_cli.exports import (
        export_timeseries_artifacts,
    )

    frame = pd.DataFrame(
        {
            "time": ["2026-06-01"],
            "value": [42.0],
            "approval_status": ["Approved"],
            "qualifier": [""],
        }
    )
    csv_header_metadata = {
        "site_no": "USGS-04193500",
        "Description": "Discharge, cubic feet per second",
        "Parameter": "00060",
        "Statistic": "00003",
        "TS_ID": "123",
        "IV_TS_ID": "",
        "Site number": "04193500",
        "Station name": "MAUMEE RIVER AT WATERVILLE OH",
        "Latitude": 41.5,
        "Longitude": -83.7,
        "HUC code": "04100009",
        "Drainage area": 6330.0,
    }

    result = export_timeseries_artifacts(
        frame,
        tmp_path,
        "discharge",
        "04193500",
        csv_header_metadata=csv_header_metadata,
    )

    lines = _read_lines(result["csv"])

    assert lines[1] == (
        '# "USGS-04193500","Discharge, cubic feet per second","00060","00003",'
        '123,,"04193500","MAUMEE RIVER AT WATERVILLE OH",41.5,-83.7,'
        '"04100009",6330.0'
    )


def test_periodic_header_quotes_text_identifier_fields(tmp_path):
    """Periodic metadata should quote station, HUC, and code-like text fields."""
    from hydrologic_toolbox_data_retrieval_cli.exports import (
        export_timeseries_artifacts,
    )

    frame = pd.DataFrame(
        {
            "time": ["2026-06-01T00:00:00Z"],
            "value": [12.5],
            "vertical_datum": ["NAVD88"],
            "approval_status": ["Approved"],
            "qualifier": [""],
            "measuring_agency": ["USGS"],
            "parameter_code": ["72019"],
        }
    )
    csv_header_metadata = {
        "monitoring_location_id": "USGS-410947071344803",
        "monitoring_location_number": "410947071344803",
        "monitoring_location_name": "RI-NHW  258 NEW SHOREHAM (BLOCK ISLAND)",
        "site_type_code": "GW",
        "hydrologic_unit_code": "01100007",
        "vertical_datum": "NAVD88",
    }

    result = export_timeseries_artifacts(
        frame,
        tmp_path,
        "gw_periodic",
        "410947071344803",
        csv_header_metadata=csv_header_metadata,
    )

    lines = _read_lines(result["csv"])

    assert lines[1] == (
        '# "USGS-410947071344803","410947071344803",'
        '"RI-NHW  258 NEW SHOREHAM (BLOCK ISLAND)","GW","01100007","NAVD88"'
    )


def test_timeseries_csv_write_replaces_existing_file(tmp_path):
    """Successful retries should replace an existing CSV with fresh output."""
    from hydrologic_toolbox_data_retrieval_cli.exports import (
        export_timeseries_artifacts,
    )

    csv_path = tmp_path / "discharge_04193500.csv"
    csv_path.write_text("old stale content\n", encoding="utf-8")
    frame = pd.DataFrame(
        {
            "time": ["2026-06-01"],
            "value": [42.0],
            "approval_status": ["Approved"],
            "qualifier": [""],
        }
    )

    export_timeseries_artifacts(frame, tmp_path, "discharge", "04193500")

    content = csv_path.read_text(encoding="utf-8")
    assert "old stale content" not in content
    assert "2026-06-01,42.0,Approved," in content


def test_atomic_csv_write_cleans_temporary_file_on_failure(tmp_path):
    """Failed writes should preserve the old final CSV and remove the temp file."""
    from hydrologic_toolbox_data_retrieval_cli.exports import _write_csv_atomically

    csv_path = tmp_path / "discharge_04193500.csv"
    csv_path.write_text("old stable content\n", encoding="utf-8")

    def failing_write(path):
        path.write_text("partial new content\n", encoding="utf-8")
        raise RuntimeError("simulated write failure")

    try:
        _write_csv_atomically(csv_path, failing_write)
    except RuntimeError as exc:
        assert str(exc) == "simulated write failure"
    else:
        raise AssertionError("Expected simulated write failure")

    assert csv_path.read_text(encoding="utf-8") == "old stable content\n"
    assert not (tmp_path / ".discharge_04193500.csv.tmp").exists()
