# Student-Success Data Quality Checks

Privacy-safe Python and SQL patterns for reviewing student-success data quality. Every example runs on **synthetic data** — this repo demonstrates *how* to check data, never with real student records.

## Why this exists

In institutional research, the most expensive mistakes are silent: a join that drops 4% of students, a GPA field that suddenly allows 9.99, a "current term" flag that points at last year. These checks are the ones I run before any analysis leaves my desk.

## What's inside

| Path | Description |
|---|---|
| `dq_checks.py` | Pandas-based check functions: null rates, duplicate keys, range/domain checks, referential integrity. Returns a structured report. |
| `dq_checks.sql` | The same checks expressed in SQL for warehouse-side validation. |
| `PRIVACY.md` | The privacy rules these patterns are designed around. |

## Quickstart

```python
import pandas as pd
from dq_checks import run_all_checks

enrollment = pd.read_csv("synthetic_enrollment.csv")   # synthetic!
terms = pd.read_csv("synthetic_terms.csv")             # synthetic!

report = run_all_checks(
    enrollment,
    key="student_id",
    reference_tables={"terms": (terms, "term_code")},
    numeric_ranges={"term_gpa": (0.0, 4.0), "credits_attempted": (0, 24)},
)
print(report.to_markdown())
```

Each check returns pass/warn/fail with the offending row count and a sample of keys — never full PII.

## The check catalog

1. **Null-rate check** — % null per column vs. an expected baseline; fails at 2× baseline.
2. **Duplicate-key check** — the grain key (`student_id` + `term`) must be unique.
3. **Range check** — numerics inside plausible bounds (GPA 0–4, credits 0–24).
4. **Domain check** — categoricals inside an allowed value list (catches "Falll 2024" typos and new codes).
5. **Referential integrity** — every foreign key exists in its parent table (orphan enrollments = dropped students downstream).
6. **Freshness check** — max load timestamp vs. expected; stale data fails loudly.

## Design rules

- Checks return **data**, not just prints — a DataFrame report you can log, trend, and alert on.
- Samples show **keys only**, capped at 5 rows. Full-row dumps of student data are never the output.
- SQL and Python versions implement the **same logic** so warehouse and analyst-layer results can be reconciled.
