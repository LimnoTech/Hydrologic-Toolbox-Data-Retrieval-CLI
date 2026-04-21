"""Artifact export helpers for sidecar time-series workflows."""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

_RAW_CSV_HEADER_FIELDS = [
    "TS_ID",
    "Parameter",
    "Statistic",
    "IV_TS_ID",
    "Description",
    "site_no",
]

_REDUCED_CSV_COLUMN_NAMES = {
    "value": "Daily values",
    "time": "Time",
    "approval_status": "Approval status",
    "qualifier": "Qualifier",
}


def _json_safe_value(value):
    """Convert pandas-style values into JSON-serializable Python values."""
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


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


def _feature_id_from_row(row, index):
    """Return a stable best-effort feature id for a tabular row."""
    for key in ("id", "monitoring_location_id", "monitoring_location_number"):
        if key in row and row[key] not in (None, ""):
            return str(row[key])
    if "time" in row and row["time"] not in (None, ""):
        return f"feature-{index}-{row['time']}"
    return f"feature-{index}"


def _row_geometry(row, geometry_enabled):
    """Return a GeoJSON geometry object or None for a tabular row."""
    if not geometry_enabled:
        return None

    geometry = row.get("geometry")
    if geometry is not None and hasattr(geometry, "__geo_interface__"):
        return geometry.__geo_interface__

    longitude = row.get("longitude", row.get("dec_long_va"))
    latitude = row.get("latitude", row.get("dec_lat_va"))
    if longitude is None or latitude is None:
        return None

    longitude = _json_safe_value(longitude)
    latitude = _json_safe_value(latitude)
    if longitude is None or latitude is None:
        return None

    return {"type": "Point", "coordinates": [longitude, latitude]}


def dataframe_to_feature_collection(frame, geometry_enabled=True):
    """Convert a pandas-style frame into a GeoJSON-like FeatureCollection."""
    if frame is None:
        rows = []
    else:
        rows = pd.DataFrame(frame.copy()).to_dict(orient="records")

    features = []
    for index, row in enumerate(rows):
        feature_id = _feature_id_from_row(row, index)
        properties = {
            key: _json_safe_value(value)
            for key, value in row.items()
            if key != "geometry"
        }
        features.append(
            {
                "type": "Feature",
                "properties": properties,
                "id": feature_id,
                "geometry": _row_geometry(row, geometry_enabled),
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "numberReturned": len(features),
    }


def export_combined_json_artifact(payload, output_dir, file_stem):
    """Write a combined raw-USGS-style JSON artifact and return its path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{file_stem}.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json_path


def export_timeseries_artifacts(
    frame,
    output_dir,
    workflow_type,
    station_id,
    json_payload=None,
    csv_header_metadata=None,
):
    """Write workflow artifacts to JSON, CSV, and parquet when available."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{workflow_type}_{station_id}.json"
    csv_path = output_dir / f"{workflow_type}_{station_id}.csv"
    parquet_path = output_dir / f"{workflow_type}_{station_id}.parquet"

    export_frame = _prepare_frame_for_export(frame)

    if json_payload is None:
        json_path.write_text(export_frame.to_json(orient="records", indent=2), encoding="utf-8")
    else:
        json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")
    _write_timeseries_csv_artifact(csv_path, export_frame, csv_header_metadata=csv_header_metadata)

    file_paths = {
        "json": json_path,
        "csv": csv_path,
        "parquet": parquet_path,
        "parquet_error": None,
    }
    try:
        export_frame.to_parquet(parquet_path, index=False)
    except Exception as exc:  # pragma: no cover - depends on parquet engine availability
        file_paths["parquet"] = None
        file_paths["parquet_error"] = str(exc)

    return file_paths


def _geometry_to_serializable(value):
    """Convert shapely-like geometry values into JSON-safe structures."""
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
        writer.writerow([f"# {_RAW_CSV_HEADER_FIELDS[0]}", *_RAW_CSV_HEADER_FIELDS[1:]])
        writer.writerow([f"# {header_values[0]}", *header_values[1:]])
        writer.writerow(reduced_frame.columns)
        for row in reduced_frame.itertuples(index=False, name=None):
            writer.writerow(row)


def format_artifact_messages(files):
    """Return a compact list of artifact paths or export warnings for display."""
    if not files:
        return ["No artifacts written because no records were returned."]

    messages = [str(files["json"]), str(files["csv"])]
    if files["parquet"] is None:
        messages.append(files["parquet_error"])
    else:
        messages.append(str(files["parquet"]))
    return messages
