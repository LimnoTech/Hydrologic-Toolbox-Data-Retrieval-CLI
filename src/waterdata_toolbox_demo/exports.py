"""Artifact export helpers for sidecar time-series workflows."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_timeseries_artifacts(frame, output_dir, workflow_type, station_id):
    """Write workflow artifacts to JSON, CSV, and parquet when available."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{workflow_type}_{station_id}.json"
    csv_path = output_dir / f"{workflow_type}_{station_id}.csv"
    parquet_path = output_dir / f"{workflow_type}_{station_id}.parquet"

    export_frame = _prepare_frame_for_export(frame)

    json_path.write_text(export_frame.to_json(orient="records", indent=2))
    export_frame.to_csv(csv_path, index=False)

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
