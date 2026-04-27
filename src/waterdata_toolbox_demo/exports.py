"""Artifact export helpers for CSV-only app workflows."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

import pandas as pd

_RAW_CSV_HEADER_FIELDS = [
    "site_no",
    "Description",
    "Parameter",
    "Statistic",
    "TS_ID",
    "IV_TS_ID",
]

_REDUCED_CSV_COLUMN_NAMES = {
    "time": "Time",
    "value": "Daily values",
    "approval_status": "Approval status",
    "qualifier": "Qualifier",
}


def _csv_safe_value(value):
    """Convert export values into CSV-friendly Python scalars."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    if isinstance(value, pd.Timestamp):
        if value.hour == 0 and value.minute == 0 and value.second == 0 and value.microsecond == 0:
            return value.strftime("%Y-%m-%d")
        return value.isoformat()
    if isinstance(value, datetime):
        if value.hour == 0 and value.minute == 0 and value.second == 0 and value.microsecond == 0:
            return value.strftime("%Y-%m-%d")
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _csv_escape_field(value, force_quote=False):
    """Return one CSV field with optional forced quoting."""
    text = str(_csv_safe_value(value))
    text = text.replace('"', '""')
    needs_quote = force_quote or any(character in text for character in [",", '"', "\n", "\r"])
    if needs_quote:
        return f'"{text}"'
    return text


def _format_csv_line(values, forced_quote_fields=None, field_names=None):
    """Return a CSV line with optional forced quoting for selected fields."""
    forced_quote_fields = set(forced_quote_fields or [])
    field_names = field_names or [None] * len(values)
    formatted_values = [
        _csv_escape_field(value, force_quote=field_name in forced_quote_fields)
        for value, field_name in zip(values, field_names)
    ]
    return ",".join(formatted_values)


def export_timeseries_artifacts(
    frame,
    output_dir,
    workflow_type,
    station_id,
    csv_header_metadata=None,
):
    """Write the packaged-app time-series CSV artifact and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{workflow_type}_{station_id}.csv"

    export_frame = _prepare_frame_for_export(frame)
    _write_timeseries_csv_artifact(csv_path, export_frame, csv_header_metadata=csv_header_metadata)
    return {"csv": csv_path}


def export_station_artifacts(frame, output_dir, file_stem):
    """Write a normalized station CSV artifact and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{file_stem}.csv"
    export_frame = _prepare_frame_for_export(frame)
    export_frame.to_csv(csv_path, index=False)
    return {"csv": csv_path}


def _geometry_to_serializable(value):
    """Convert shapely-like geometry values into CSV-safe structures."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if hasattr(value, "__geo_interface__"):
        geo = value.__geo_interface__
        return geo.get("coordinates", geo)

    return value


def _prepare_frame_for_export(frame):
    """Flatten geometry-bearing frames into export-friendly tabular data."""
    if not isinstance(frame, pd.DataFrame):
        return frame

    export_frame = pd.DataFrame(frame.copy())
    if "geometry" in export_frame.columns:
        geometry_series = export_frame["geometry"]
        if "geometry_type" not in export_frame.columns:
            export_frame["geometry_type"] = geometry_series.map(
                lambda value: getattr(value, "geom_type", None)
            )
        export_frame["geometry"] = geometry_series.map(_geometry_to_serializable)

    return export_frame


def _prepare_reduced_timeseries_csv_frame(frame):
    """Return the reduced add-data CSV body requested by the user."""
    if not isinstance(frame, pd.DataFrame):
        return frame

    reduced_frame = pd.DataFrame(frame.copy())
    for source_column in _REDUCED_CSV_COLUMN_NAMES:
        if source_column not in reduced_frame.columns:
            reduced_frame[source_column] = pd.NA

    reduced_frame = reduced_frame[list(_REDUCED_CSV_COLUMN_NAMES)].rename(
        columns=_REDUCED_CSV_COLUMN_NAMES
    )
    for column in reduced_frame.columns:
        reduced_frame[column] = reduced_frame[column].map(_csv_safe_value)
    return reduced_frame


def _write_timeseries_csv_artifact(csv_path, frame, csv_header_metadata=None):
    """Write either the legacy full-frame CSV or the new reduced raw-header CSV."""
    if csv_header_metadata is None:
        frame.to_csv(csv_path, index=False)
        return

    reduced_frame = _prepare_reduced_timeseries_csv_frame(frame)
    header_values = [_csv_safe_value(csv_header_metadata.get(key)) for key in _RAW_CSV_HEADER_FIELDS]

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        handle.write(
            "# "
            + _format_csv_line(
                _RAW_CSV_HEADER_FIELDS,
                field_names=_RAW_CSV_HEADER_FIELDS,
            )
            + "\n"
        )
        handle.write(
            "# "
            + _format_csv_line(
                header_values,
                forced_quote_fields={"Parameter", "Statistic"},
                field_names=_RAW_CSV_HEADER_FIELDS,
            )
            + "\n"
        )
        writer.writerow(reduced_frame.columns)
        for row in reduced_frame.itertuples(index=False, name=None):
            writer.writerow(row)


def format_artifact_messages(files):
    """Return a compact list of artifact paths or export warnings for display."""
    if not files:
        return ["No artifacts written because no records were returned."]

    return [str(path) for path in files.values() if path is not None]
