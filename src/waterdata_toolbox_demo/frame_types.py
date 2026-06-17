"""DataFrame dtype helpers for Water Data workflow outputs."""

from __future__ import annotations

import pandas as pd


def categorize_existing_columns(frame, column_names):
    """Convert selected existing DataFrame columns to pandas categorical dtype."""
    category_dtype = pd.CategoricalDtype()
    for column_name in column_names:
        if column_name not in frame.columns:
            continue
        if str(frame[column_name].dtype) == "category":
            continue
        frame[column_name] = frame[column_name].astype(category_dtype)
    return frame
