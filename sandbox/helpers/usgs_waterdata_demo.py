"""Support utilities for the USGS Water Data demo notebook."""

from pathlib import Path
import warnings

import pandas as pd


DEMO_CONFIG = {
    "bbox": (-82.859, 31.899, -82.013, 32.947),
    "output_dir": "outputs/usgs_waterdata_demo",
    "date_range": ("1880-01-01", "2100-01-01"),
    "example_stations": {
        "discharge": {"station_id": "02225500", "parameter_code": "00060"},
        "gw_daily": {"station_id": "324209082430201", "parameter_code": "72019"},
        "gw_periodic": {"station_id": "410947071344803", "parameter_code": "72019"},
    },
}

LEGACY_CALLS = {
    "discharge": {
        "legacy_steps": ["New Project station discovery", "Adding Data to Project"],
    },
    "gw_daily": {
        "legacy_steps": ["New Project station discovery", "Adding Data to Project"],
    },
    "gw_periodic": {
        "legacy_steps": ["New Project station discovery", "Adding Data to Project"],
    },
}

NOTEBOOK_MAPPING_ROWS = [
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "discharge",
        "legacy_intent": "Find surface-water stations in a bounding box",
        "modern_demo_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=ST, parameter_code=00060",
        "expected_output_shape": "DataFrame of discharge-capable stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_daily",
        "legacy_intent": "Find groundwater stations with daily series in a bounding box",
        "modern_demo_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_time_series_metadata",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater daily stations",
    },
    {
        "legacy_workflow_step": "New Project station discovery",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Find groundwater stations with periodic observations in a bounding box",
        "modern_demo_entry_point": "get_usgs_stations_in_bbox",
        "waterdata_calls": "get_monitoring_locations + get_field_measurements",
        "important_filters": "site_type_code=GW",
        "expected_output_shape": "DataFrame of groundwater periodic stations",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "discharge",
        "legacy_intent": "Retrieve discharge time series for a selected station",
        "modern_demo_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "parameter_code=00060, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_daily",
        "legacy_intent": "Retrieve groundwater daily time series for a selected station",
        "modern_demo_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_daily",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
    {
        "legacy_workflow_step": "Adding Data to Project",
        "workflow_type": "gw_periodic",
        "legacy_intent": "Retrieve groundwater periodic measurements for a selected station",
        "modern_demo_entry_point": "get_usgs_timeseries",
        "waterdata_calls": "get_field_measurements",
        "important_filters": "configured parameter_code, configured date_range",
        "expected_output_shape": "normalized DataFrame + records + files",
    },
]

_INFER_FORMAT_WARNING_PATTERN = (
    r"Could not infer format, so each element will be parsed individually.*"
)


def export_timeseries_artifacts(frame, output_dir, workflow_type, station_id):
    """Write demo time-series artifacts to JSON, CSV, and parquet when available."""
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
    """Convert shapely-like geometry objects into JSON-serializable structures."""
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


def _call_station_discovery_with_filtered_datetime_warning(function, **kwargs):
    """Call a waterdata discovery function while silencing the known date warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_INFER_FORMAT_WARNING_PATTERN,
            category=UserWarning,
        )
        return function(**kwargs)


def _extract_decimal_coordinate(value, axis):
    """Extract a latitude or longitude value from coordinate-like objects."""
    if value is None:
        return pd.NA

    coord = getattr(value, "y" if axis == "lat" else "x", None)
    if coord is not None:
        return coord

    if hasattr(value, "__geo_interface__"):
        coordinates = value.__geo_interface__.get("coordinates")
        if coordinates and len(coordinates) >= 2:
            return coordinates[1] if axis == "lat" else coordinates[0]

    return pd.NA


def _load_geopandas():
    """Import GeoPandas only when station discovery needs GeoDataFrame support."""
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "Install `geopandas` to use GeoDataFrame station discovery support."
        ) from exc
    return gpd


def _to_station_geodataframe(frame):
    """Convert a normalized station frame into an EPSG:4326 GeoDataFrame."""
    gpd = _load_geopandas()
    station_frame = frame.copy()

    station_frame["dec_long_va"] = pd.to_numeric(
        station_frame.get("dec_long_va"), errors="coerce"
    )
    station_frame["dec_lat_va"] = pd.to_numeric(
        station_frame.get("dec_lat_va"), errors="coerce"
    )

    existing_geometry = station_frame.get("geometry")
    if existing_geometry is not None and existing_geometry.notna().any():
        geometry = gpd.GeoSeries(existing_geometry, index=station_frame.index, crs="EPSG:4326")
        station_frame = station_frame.drop(columns=["geometry"])
    else:
        geometry_values = pd.Series([None] * len(station_frame), index=station_frame.index)
        valid_geometry = (
            station_frame["dec_long_va"].notna() & station_frame["dec_lat_va"].notna()
        )
        if valid_geometry.any():
            geometry_values.loc[valid_geometry] = list(
                gpd.points_from_xy(
                    station_frame.loc[valid_geometry, "dec_long_va"],
                    station_frame.loc[valid_geometry, "dec_lat_va"],
                )
            )
        geometry = gpd.GeoSeries(geometry_values, index=station_frame.index, crs="EPSG:4326")

    return gpd.GeoDataFrame(station_frame, geometry=geometry, crs="EPSG:4326")


def _normalize_station_frame(candidate_frame, qualifying_frame, workflow_type):
    """Reshape discovered stations into the legacy-style preview columns used by the notebook."""
    candidate_ids = set(candidate_frame["monitoring_location_id"])
    qualifying_ids = set(qualifying_frame["monitoring_location_id"])
    frame = candidate_frame[
        candidate_frame["monitoring_location_id"].isin(candidate_ids & qualifying_ids)
    ].copy()
    frame["workflow_type"] = workflow_type
    frame = frame.drop_duplicates(subset=["monitoring_location_id"])
    frame = frame.sort_values("monitoring_location_id").reset_index(drop=True)

    if frame.empty and "workflow_type" not in frame.columns:
        frame["workflow_type"] = pd.Series(dtype="object")

    if "site_no" not in frame.columns:
        if "monitoring_location_number" in frame.columns:
            frame["site_no"] = frame["monitoring_location_number"]
        elif "monitoring_location_id" in frame.columns:
            frame["site_no"] = frame["monitoring_location_id"].astype(str).str.replace(
                r"^USGS-", "", regex=True
            )
        else:
            frame["site_no"] = pd.Series(dtype="object")

    if "station_nm" not in frame.columns:
        if "monitoring_location_name" in frame.columns:
            frame["station_nm"] = frame["monitoring_location_name"]
        elif "location_name" in frame.columns:
            frame["station_nm"] = frame["location_name"]
        else:
            frame["station_nm"] = pd.Series(dtype="object")

    if "site_tp_cd" not in frame.columns:
        if "site_type_code" in frame.columns:
            frame["site_tp_cd"] = frame["site_type_code"]
        else:
            frame["site_tp_cd"] = pd.Series(dtype="object")

    if "dec_lat_va" not in frame.columns:
        if "latitude" in frame.columns:
            frame["dec_lat_va"] = frame["latitude"]
        elif "geometry" in frame.columns:
            frame["dec_lat_va"] = frame["geometry"].map(
                lambda value: _extract_decimal_coordinate(value, "lat")
            )
        else:
            frame["dec_lat_va"] = pd.Series([pd.NA] * len(frame), dtype="object")

    if "dec_long_va" not in frame.columns:
        if "longitude" in frame.columns:
            frame["dec_long_va"] = frame["longitude"]
        elif "geometry" in frame.columns:
            frame["dec_long_va"] = frame["geometry"].map(
                lambda value: _extract_decimal_coordinate(value, "lon")
            )
        else:
            frame["dec_long_va"] = pd.Series([pd.NA] * len(frame), dtype="object")

    if "state_cd" not in frame.columns:
        if "state_code" in frame.columns:
            frame["state_cd"] = frame["state_code"]
        else:
            frame["state_cd"] = pd.Series(dtype="object")

    if "county_cd" not in frame.columns:
        if "county_code" in frame.columns:
            frame["county_cd"] = frame["county_code"]
        else:
            frame["county_cd"] = pd.Series(dtype="object")

    return _to_station_geodataframe(frame)


def _prepare_station_plot_frame(frame):
    """Coerce station preview coordinates into numeric longitude and latitude columns."""
    plot_frame = frame.copy()
    plot_frame["dec_long_va"] = pd.to_numeric(plot_frame["dec_long_va"], errors="coerce")
    plot_frame["dec_lat_va"] = pd.to_numeric(plot_frame["dec_lat_va"], errors="coerce")
    plot_frame = plot_frame.dropna(subset=["dec_long_va", "dec_lat_va"]).reset_index(
        drop=True
    )
    return plot_frame


def _combined_web_mercator_extent(frames):
    """Return (xmin, ymin, xmax, ymax) in EPSG:3857 across all GeoDataFrames."""
    import numpy as np
    bounds = []
    for frame in frames:
        if not (hasattr(frame, "crs") and "geometry" in frame.columns) or frame.empty:
            continue
        b = frame.to_crs(epsg=3857).total_bounds  # (xmin, ymin, xmax, ymax)
        bounds.append(b)
    if not bounds:
        return None
    arr = np.array(bounds)
    return (arr[:, 0].min(), arr[:, 1].min(), arr[:, 2].max(), arr[:, 3].max())


def plot_station_discovery_map(
    workflow_type,
    create_section_results,
    plt_module=None,
    prepare_station_plot_frame=None,
    shared_extent=None,
):
    """Plot station locations for the selected new-project workflow."""
    if prepare_station_plot_frame is None:
        prepare_station_plot_frame = _prepare_station_plot_frame
    if plt_module is None:
        import matplotlib.pyplot as plt_module

    frame = create_section_results[workflow_type]
    if frame.empty:
        print(f"No stations available to plot for {workflow_type}")
        return

    plot_frame = prepare_station_plot_frame(frame)
    if plot_frame.empty:
        print(f"No mappable station coordinates available for {workflow_type}")
        return

    fig, ax = plt_module.subplots(figsize=(10, 8))

    has_geometry = hasattr(plot_frame, "crs") and "geometry" in plot_frame.columns
    if has_geometry:
        web_mercator_frame = plot_frame.to_crs(epsg=3857)
        web_mercator_frame.plot(ax=ax, markersize=12, color="steelblue", zorder=2)
        if shared_extent is not None:
            xmin, ymin, xmax, ymax = shared_extent
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
        try:
            import contextily as ctx
            ctx.add_basemap(ax, source=ctx.providers.Esri.WorldTopoMap, zoom_adjust=-1)
        except ImportError:
            pass
    else:
        ax.scatter(plot_frame["dec_long_va"], plot_frame["dec_lat_va"])

    ax.set_title(f"{workflow_type.replace('_', ' ').title()} Station Discovery")
    ax.set_axis_off()
    plt_module.tight_layout()
    plt_module.show()


def render_station_discovery_selector(
    create_section_results,
    widgets_module=None,
    display_fn=None,
    clear_output_fn=None,
    plot_station_discovery_map_fn=None,
):
    """Render the create-project workflow selector and station map widget."""
    if widgets_module is None:
        import ipywidgets as widgets_module
    if display_fn is None:
        from IPython.display import display as display_fn
    if clear_output_fn is None:
        from IPython.display import clear_output as clear_output_fn
    if plot_station_discovery_map_fn is None:
        plot_station_discovery_map_fn = plot_station_discovery_map

    shared_extent = _combined_web_mercator_extent(list(create_section_results.values()))

    options = list(create_section_results.keys()) or ["discharge", "gw_daily", "gw_periodic"]
    dropdown = widgets_module.Dropdown(
        options=options,
        value=options[0],
        description="Workflow:",
    )
    output = widgets_module.Output()

    def _render(change=None):
        with output:
            clear_output_fn(wait=True)
            plot_station_discovery_map_fn(
                dropdown.value, create_section_results, shared_extent=shared_extent
            )

    dropdown.observe(_render, names="value")
    _render()
    display_fn(widgets_module.VBox([dropdown, output]))


def _normalize_monitoring_location_id(station_id):
    """Return the USGS-prefixed monitoring location id expected by waterdata calls."""
    return station_id if station_id.startswith("USGS-") else f"USGS-{station_id}"


def _call_waterdata_with_filtered_datetime_warning(function, **kwargs):
    """Call a waterdata retrieval function while silencing the known date warning."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=_INFER_FORMAT_WARNING_PATTERN,
            category=UserWarning,
        )
        return function(**kwargs)


def _prepare_plot_frame(payload):
    """Normalize payload time/value columns into a sorted plotting frame."""
    frame = payload["frame"].copy()
    time_values = frame["time"]
    if pd.api.types.is_numeric_dtype(time_values):
        parsed_time = pd.to_datetime(time_values, unit="ms", errors="coerce")
    else:
        parsed_time = pd.to_datetime(time_values, errors="coerce")
        numeric_time = pd.to_numeric(time_values, errors="coerce")
        needs_epoch_parse = parsed_time.isna() & numeric_time.notna()
        if needs_epoch_parse.any():
            parsed_time.loc[needs_epoch_parse] = pd.to_datetime(
                numeric_time.loc[needs_epoch_parse],
                unit="ms",
                errors="coerce",
            )
    frame["time"] = parsed_time
    frame = frame.dropna(subset=["time", "value"]).sort_values("time").reset_index(drop=True)
    return frame


def plot_generated_output(
    workflow_type,
    add_data_results,
    plt_module=None,
    prepare_plot_frame=None,
):
    """Plot the selected add-data workflow output as a simple time series."""
    if prepare_plot_frame is None:
        prepare_plot_frame = _prepare_plot_frame
    if plt_module is None:
        import matplotlib.pyplot as plt_module

    result = add_data_results[workflow_type]
    if result["error"] or result["payload"] is None:
        print(f"Warning: no plot available for {workflow_type}")
        return

    frame = prepare_plot_frame(result["payload"])
    if frame.empty:
        print(f"No rows available to plot for {workflow_type}")
        return

    unit = None
    if "unit_of_measure" in frame.columns and not frame["unit_of_measure"].dropna().empty:
        unit = frame["unit_of_measure"].dropna().iloc[0]

    station_id = None
    if "station_id" in frame.columns and not frame["station_id"].dropna().empty:
        station_id = frame["station_id"].dropna().iloc[0]

    title = workflow_type.replace("_", " ").title()
    if station_id:
        title = f"{title} ({station_id})"

    fig, ax = plt_module.subplots(figsize=(10, 4))
    ax.plot(frame["time"], frame["value"], marker="o")
    ax.set_title(title)
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Value ({unit})" if unit else "Value")
    ax.grid(True)
    plt_module.xticks(rotation=30)
    plt_module.tight_layout()
    plt_module.show()


def render_plot_selector(
    add_data_results,
    widgets_module=None,
    display_fn=None,
    clear_output_fn=None,
    plot_generated_output_fn=None,
):
    """Render the add-data workflow selector and time-series plot widget."""
    if widgets_module is None:
        import ipywidgets as widgets_module
    if display_fn is None:
        from IPython.display import display as display_fn
    if clear_output_fn is None:
        from IPython.display import clear_output as clear_output_fn
    if plot_generated_output_fn is None:
        plot_generated_output_fn = plot_generated_output

    options = list(add_data_results.keys()) or ["discharge", "gw_daily", "gw_periodic"]
    dropdown = widgets_module.Dropdown(
        options=options,
        value=options[0],
        description="Workflow:",
    )
    output = widgets_module.Output()

    def _render(change=None):
        with output:
            clear_output_fn(wait=True)
            plot_generated_output_fn(dropdown.value, add_data_results)

    dropdown.observe(_render, names="value")
    _render()
    display_fn(widgets_module.VBox([dropdown, output]))
