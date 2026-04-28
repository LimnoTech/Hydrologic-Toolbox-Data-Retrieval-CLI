"""Non-widget plotting helpers shared by the sidecar workflows."""

from __future__ import annotations

import pandas as pd


def prepare_plot_frame(payload):
    """Normalize payload time/value columns into a sorted plotting frame."""
    frame = payload["frame"].copy()
    time_values = frame["time"]
    if pd.api.types.is_numeric_dtype(time_values):
        parsed_time = pd.to_datetime(time_values, unit="ms", errors="coerce", utc=True)
    else:
        numeric_time = pd.to_numeric(time_values, errors="coerce")
        parsed_time = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]")
        numeric_mask = numeric_time.notna()
        if numeric_mask.any():
            parsed_time.loc[numeric_mask] = pd.to_datetime(
                numeric_time.loc[numeric_mask],
                unit="ms",
                errors="coerce",
                utc=True,
            )
        if (~numeric_mask).any():
            parsed_time.loc[~numeric_mask] = pd.to_datetime(
                time_values.loc[~numeric_mask],
                errors="coerce",
                utc=True,
            )
    frame["time"] = parsed_time
    frame = frame.dropna(subset=["time", "value"]).sort_values("time").reset_index(drop=True)
    return frame
