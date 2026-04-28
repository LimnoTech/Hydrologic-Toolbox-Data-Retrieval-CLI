"""Artifact export helpers for CSV-only app workflows."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapefile

_RAW_CSV_HEADER_FIELDS = [
    "site_no",
    "Description",
    "Parameter",
    "Statistic",
    "TS_ID",
    "IV_TS_ID",
    "Site number",
    "Station name",
    "Latitude",
    "Longitude",
    "HUC code",
    "Drainage area",
]

_REDUCED_CSV_COLUMN_NAMES = {
    "time": "Time",
    "value": "Daily values",
    "approval_status": "Approval status",
    "qualifier": "Qualifier",
}

_STATION_SHAPEFILE_EXCLUDED_FIELDS = {
    "geometry",
    "workflow_type",
    "geometry_type",
}

_WGS84_PRJ = (
    'GEOGCS["WGS 84",DATUM["WGS_1984",'
    'SPHEROID["WGS 84",6378137,298.257223563]],'
    'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
)


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


def _dbf_text_value(value):
    """Return a DBF-safe string value."""
    safe_value = _csv_safe_value(value)
    return "" if safe_value == "" else str(safe_value)


def _dbf_safe_value(value, field_type):
    """Return a DBF-safe scalar value for one shapefile field type."""
    if value is None:
        return "" if field_type == "C" else None

    try:
        if pd.isna(value):
            return "" if field_type == "C" else None
    except Exception:
        pass

    if hasattr(value, "item"):
        try:
            value = value.item()
        except Exception:
            pass

    if field_type == "C":
        return _dbf_text_value(value)
    if field_type == "L":
        return bool(value) if value is not None else None
    return value


def _raw_station_attribute_columns(frame):
    """Return the raw station columns that should be written to the DBF table."""
    return [
        column_name
        for column_name in frame.columns
        if column_name not in _STATION_SHAPEFILE_EXCLUDED_FIELDS
    ]


def _truncate_shapefile_field_names(column_names):
    """Return a deterministic shapefile-safe field-name mapping."""
    used_names = set()
    field_name_map = {}

    for column_name in column_names:
        if len(column_name) <= 10 and column_name not in used_names:
            field_name_map[column_name] = column_name
            used_names.add(column_name)
            continue

        candidate = column_name[:10]
        if candidate not in used_names:
            field_name_map[column_name] = candidate
            used_names.add(candidate)
            continue

        suffix_index = 1
        while True:
            suffix = f"_{suffix_index}"
            base_length = 10 - len(suffix)
            candidate = f"{column_name[:base_length]}{suffix}"
            if candidate not in used_names:
                field_name_map[column_name] = candidate
                used_names.add(candidate)
                break
            suffix_index += 1

    return field_name_map


def _series_is_boolean_like(series):
    """Return True when a series contains only boolean-like values."""
    if pd.api.types.is_bool_dtype(series):
        return True

    non_null = series.dropna()
    if non_null.empty:
        return False

    for value in non_null:
        if hasattr(value, "item"):
            try:
                value = value.item()
            except Exception:
                pass
        if not isinstance(value, bool):
            return False
    return True


def _infer_shapefile_field_spec(series):
    """Return a pyshp field spec for one raw station column."""
    if _series_is_boolean_like(series):
        return ("L", 1, 0)

    if pd.api.types.is_integer_dtype(series):
        return ("N", 18, 0)

    if pd.api.types.is_float_dtype(series):
        return ("F", 18, 8)

    if pd.api.types.is_datetime64_any_dtype(series):
        max_length = max((len(_dbf_text_value(value)) for value in series.dropna()), default=1)
        return ("C", min(max(max_length, 1), 254), 0)

    max_length = max((len(_dbf_text_value(value)) for value in series.dropna()), default=1)
    return ("C", min(max(max_length, 1), 254), 0)


def _station_shapefile_field_specs(frame):
    """Return the raw-column to shapefile-field spec mapping for station export."""
    attribute_columns = _raw_station_attribute_columns(frame)
    field_name_map = _truncate_shapefile_field_names(attribute_columns)
    field_specs = []
    for column_name in attribute_columns:
        field_type, field_size, field_decimal = _infer_shapefile_field_spec(frame[column_name])
        field_specs.append(
            {
                "source_name": column_name,
                "field_name": field_name_map[column_name],
                "field_type": field_type,
                "field_size": field_size,
                "field_decimal": field_decimal,
            }
        )
    return field_specs


def _geometry_xy(value):
    """Extract point coordinates from a shapely-like geometry value."""
    if value is None:
        raise ValueError("Station shapefile export requires point geometry for every row.")

    x_coord = getattr(value, "x", None)
    y_coord = getattr(value, "y", None)
    if x_coord is not None and y_coord is not None:
        return float(x_coord), float(y_coord)

    if hasattr(value, "__geo_interface__"):
        coordinates = value.__geo_interface__.get("coordinates")
        if coordinates and len(coordinates) >= 2:
            return float(coordinates[0]), float(coordinates[1])

    raise ValueError("Station shapefile export requires point geometry for every row.")


def _write_station_shapefile(writer_path, frame):
    """Write the rawer point shapefile payload using a pure-Python writer."""
    writer = shapefile.Writer(str(writer_path), shapeType=shapefile.POINT)
    writer.autoBalance = 1
    field_specs = _station_shapefile_field_specs(frame)

    for spec in field_specs:
        writer.field(
            spec["field_name"],
            spec["field_type"],
            size=spec["field_size"],
            decimal=spec["field_decimal"],
        )

    for row in frame.itertuples(index=False):
        row_mapping = row._asdict()
        x_coord, y_coord = _geometry_xy(row_mapping["geometry"])
        writer.point(x_coord, y_coord)
        writer.record(
            *[
                _dbf_safe_value(row_mapping[spec["source_name"]], spec["field_type"])
                for spec in field_specs
            ]
        )

    writer.close()


def _write_station_shapefile_sidecars(shapefile_path):
    """Write the `.prj` and `.cpg` sidecars for the station shapefile."""
    shapefile_path.with_suffix(".prj").write_text(_WGS84_PRJ, encoding="utf-8")
    shapefile_path.with_suffix(".cpg").write_text("UTF-8\n", encoding="utf-8")


def export_station_shapefile_artifacts(frame, output_dir, file_stem):
    """Write a shapefile with raw monitoring-location attributes and return the `.shp` path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shapefile_path = output_dir / f"{file_stem}.shp"
    if not isinstance(frame, gpd.GeoDataFrame):
        raise TypeError("Station shapefile export requires a GeoDataFrame with geometry.")
    export_frame = gpd.GeoDataFrame(frame.copy(), geometry="geometry", crs=frame.crs or "EPSG:4326")
    _write_station_shapefile(shapefile_path, export_frame)
    _write_station_shapefile_sidecars(shapefile_path)
    return {"shp": shapefile_path}


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
