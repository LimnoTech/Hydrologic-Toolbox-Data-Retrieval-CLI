"""DataFrame dtype helpers for Water Data workflow outputs."""

from __future__ import annotations

import pandas as pd


def _is_missing(value):
    """Return whether a scalar-like value is missing without tripping on lists."""
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _has_only_hashable_values(series):
    """Return whether every non-missing value in a series can be a category."""
    for value in series:
        if _is_missing(value):
            continue
        try:
            hash(value)
        except TypeError:
            return False
    return True


def categorize_existing_columns(frame, column_names):
    """Convert selected existing DataFrame columns to pandas categorical dtype."""
    category_dtype = pd.CategoricalDtype()
    for column_name in column_names:
        if column_name not in frame.columns:
            continue
        if str(frame[column_name].dtype) == "category":
            continue
        if not _has_only_hashable_values(frame[column_name]):
            continue
        frame[column_name] = frame[column_name].astype(category_dtype)
    return frame
