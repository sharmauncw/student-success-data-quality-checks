"""Reusable data-quality checks for synthetic student-success datasets."""

from __future__ import annotations

import pandas as pd


def null_rate_report(df: pd.DataFrame) -> pd.DataFrame:
    """Return null counts and null rates for each column."""
    return (
        pd.DataFrame(
            {
                "column": df.columns,
                "null_count": df.isna().sum().values,
                "null_rate": df.isna().mean().values,
            }
        )
        .sort_values(["null_rate", "column"], ascending=[False, True])
        .reset_index(drop=True)
    )


def duplicate_key_report(df: pd.DataFrame, key_columns: list[str]) -> pd.DataFrame:
    """Return duplicated records by key columns."""
    duplicated = df[df.duplicated(key_columns, keep=False)].copy()
    if duplicated.empty:
        return pd.DataFrame(columns=key_columns + ["duplicate_count"])

    return (
        duplicated.groupby(key_columns)
        .size()
        .reset_index(name="duplicate_count")
        .sort_values("duplicate_count", ascending=False)
    )


def out_of_range_report(
    df: pd.DataFrame, column: str, minimum: float | None = None, maximum: float | None = None
) -> pd.DataFrame:
    """Return rows where a numeric column is outside expected bounds."""
    mask = pd.Series(False, index=df.index)
    if minimum is not None:
        mask = mask | (df[column] < minimum)
    if maximum is not None:
        mask = mask | (df[column] > maximum)
    return df.loc[mask].copy()

