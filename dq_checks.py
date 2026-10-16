"""
dq_checks.py — Privacy-safe data-quality checks for student-success datasets.

Each check inspects a pandas DataFrame and returns a row in a structured
report. Samples are limited to key columns (never full PII). Designed to run
on SYNTHETIC data for demonstration; the same functions apply to real extracts
inside a secured environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

MAX_SAMPLE_KEYS = 5


@dataclass
class CheckResult:
    check: str
    column: str
    status: str  # "pass" | "warn" | "fail"
    detail: str
    offending_rows: int = 0
    sample_keys: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "check": self.check,
            "column": self.column,
            "status": self.status,
            "detail": self.detail,
            "offending_rows": self.offending_rows,
            "sample_keys": self.sample_keys,
        }


def _sample_keys(df: pd.DataFrame, mask: pd.Series, key: str) -> List[str]:
    if key in df.columns:
        return df.loc[mask, key].astype(str).head(MAX_SAMPLE_KEYS).tolist()
    return df.loc[mask].index.astype(str).head(MAX_SAMPLE_KEYS).tolist()


def check_null_rates(
    df: pd.DataFrame,
    key: str,
    baselines: Optional[Dict[str, float]] = None,
    fail_multiplier: float = 2.0,
) -> List[CheckResult]:
    """Flag columns whose null rate exceeds 2x their expected baseline."""
    baselines = baselines or {}
    results = []
    for col in df.columns:
        null_rate = float(df[col].isna().mean())
        baseline = baselines.get(col, 0.01)
        if null_rate > baseline * fail_multiplier and null_rate > 0:
            status = "fail" if null_rate > 0.05 else "warn"
            mask = df[col].isna()
            results.append(CheckResult(
                check="null_rate", column=col, status=status,
                detail=f"null rate {null_rate:.2%} vs baseline {baseline:.2%}",
                offending_rows=int(mask.sum()),
                sample_keys=_sample_keys(df, mask, key),
            ))
    return results


def check_duplicate_keys(df: pd.DataFrame, key_columns: List[str]) -> List[CheckResult]:
    """The grain key must be unique — duplicates silently inflate headcounts."""
    dup_mask = df.duplicated(subset=key_columns, keep=False)
    n_dup = int(dup_mask.sum())
    status = "fail" if n_dup else "pass"
    key_label = "+".join(key_columns)
    sample = df.loc[dup_mask, key_columns].astype(str).agg("-".join, axis=1).head(MAX_SAMPLE_KEYS).tolist()
    return [CheckResult(
        check="duplicate_keys", column=key_label, status=status,
        detail=f"{n_dup} duplicate rows on key ({key_label})" if n_dup else "key is unique",
        offending_rows=n_dup, sample_keys=sample,
    )]


def check_numeric_ranges(
    df: pd.DataFrame, key: str, ranges: Dict[str, Tuple[float, float]]
) -> List[CheckResult]:
    """Numerics must fall inside plausible bounds (e.g. GPA 0–4)."""
    results = []
    for col, (lo, hi) in ranges.items():
        if col not in df.columns:
            continue
        mask = df[col].notna() & ((df[col] < lo) | (df[col] > hi))
        n_bad = int(mask.sum())
        results.append(CheckResult(
            check="range", column=col,
            status="fail" if n_bad else "pass",
            detail=f"{n_bad} values outside [{lo}, {hi}]" if n_bad else f"all values in [{lo}, {hi}]",
            offending_rows=n_bad,
            sample_keys=_sample_keys(df, mask, key),
        ))
    return results


def check_domains(
    df: pd.DataFrame, key: str, domains: Dict[str, List[str]]
) -> List[CheckResult]:
    """Categoricals must belong to the allowed value list (catches typos/new codes)."""
    results = []
    for col, allowed in domains.items():
        if col not in df.columns:
            continue
        mask = df[col].notna() & (~df[col].isin(allowed))
        n_bad = int(mask.sum())
        unexpected = df.loc[mask, col].unique().tolist()[:5] if n_bad else []
        results.append(CheckResult(
            check="domain", column=col,
            status="fail" if n_bad else "pass",
            detail=f"unexpected values: {unexpected}" if n_bad else "all values in domain",
            offending_rows=n_bad,
            sample_keys=_sample_keys(df, mask, key),
        ))
    return results


def check_referential_integrity(
    df: pd.DataFrame,
    key: str,
    reference_tables: Dict[str, Tuple[pd.DataFrame, str]],
    fk_map: Dict[str, str],
) -> List[CheckResult]:
    """Every foreign key must exist in its parent table.

    reference_tables: {"terms": (terms_df, "term_code")}
    fk_map: {"term_code": "terms"}  (child column -> reference table name)
    """
    results = []
    for fk_col, ref_name in fk_map.items():
        ref_df, ref_key = reference_tables[ref_name]
        valid = set(ref_df[ref_key].dropna().unique())
        mask = df[fk_col].notna() & (~df[fk_col].isin(valid))
        n_orphan = int(mask.sum())
        results.append(CheckResult(
            check="referential_integrity", column=fk_col,
            status="fail" if n_orphan else "pass",
            detail=(f"{n_orphan} orphan keys not in {ref_name}.{ref_key}"
                    if n_orphan else f"all keys resolve in {ref_name}.{ref_key}"),
            offending_rows=n_orphan,
            sample_keys=_sample_keys(df, mask, key),
        ))
    return results


def check_freshness(
    df: pd.DataFrame, ts_column: str, max_age_days: int = 2
) -> List[CheckResult]:
    """Data must be fresh — stale extracts fail loudly, not silently."""
    if ts_column not in df.columns:
        return [CheckResult("freshness", ts_column, "warn", "timestamp column missing")]
    latest = pd.to_datetime(df[ts_column]).max()
    age_days = (datetime.now() - latest).days
    status = "fail" if age_days > max_age_days else "pass"
    return [CheckResult(
        check="freshness", column=ts_column, status=status,
        detail=f"latest load {latest.date()} ({age_days}d ago; max {max_age_days}d)",
    )]


def run_all_checks(
    df: pd.DataFrame,
    key: str,
    key_columns: Optional[List[str]] = None,
    baselines: Optional[Dict[str, float]] = None,
    numeric_ranges: Optional[Dict[str, Tuple[float, float]]] = None,
    domains: Optional[Dict[str, List[str]]] = None,
    reference_tables: Optional[Dict[str, Tuple[pd.DataFrame, str]]] = None,
    fk_map: Optional[Dict[str, str]] = None,
    ts_column: Optional[str] = None,
) -> pd.DataFrame:
    """Run the full suite and return a structured report DataFrame."""
    results: List[CheckResult] = []
    results += check_null_rates(df, key, baselines)
    results += check_duplicate_keys(df, key_columns or [key])
    if numeric_ranges:
        results += check_numeric_ranges(df, key, numeric_ranges)
    if domains:
        results += check_domains(df, key, domains)
    if reference_tables and fk_map:
        results += check_referential_integrity(df, key, reference_tables, fk_map)
    if ts_column:
        results += check_freshness(df, ts_column)
    report = pd.DataFrame([r.as_dict() for r in results])
    return report.sort_values(["status", "check"]).reset_index(drop=True)
