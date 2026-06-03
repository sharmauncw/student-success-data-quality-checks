# Student Success Data Quality Checks

Python and SQL patterns for checking higher-education data quality before using data in reports, dashboards, or student-success models.

This project is designed for public portfolio use with synthetic data only.

## Why This Matters

Student-success analytics depends on trustworthy data. Before building a retention model or dashboard, core fields should be checked for completeness, consistency, duplicates, and timing issues.

## Planned Checks

| Check | Why it matters |
| --- | --- |
| Missing student identifiers | Prevents count errors and broken joins |
| Duplicate student-term records | Prevents inflated enrollment or course counts |
| Invalid term codes | Protects cohort and time-window logic |
| Missing course outcomes | Affects pass/fail/withdrawal indicators |
| Inconsistent college/major labels | Affects college-level dashboards |
| Unexpected null rates | Identifies fields that may not be ready for modeling |
| Out-of-range credit hours | Flags possible data-entry or join issues |

## Planned Outputs

- reusable Python validation script
- SQL check examples
- synthetic test dataset
- summary report template

## Status

Starter project. Next steps:

1. Create synthetic student-term data.
2. Add Python checks.
3. Add SQL equivalents.
4. Add a sample data-quality report.

