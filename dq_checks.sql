/* =====================================================================
   dq_checks.sql — Warehouse-side data-quality checks for student-success data.

   Mirrors dq_checks.py so analyst-layer and warehouse results can be
   reconciled. Run against SYNTHETIC data for demonstration.
   Convention: each check returns check_name, column_name, status,
   offending_rows, and a 5-row sample of keys (never full PII).
   ===================================================================== */

-- Parameters: point these at your (synthetic) tables
--   :enrollment_tbl  e.g. synthetic_enrollment
--   :terms_tbl       e.g. synthetic_terms

/* ---- 1. Null-rate check: columns exceeding 2x expected baseline ---- */
WITH nulls AS (
    SELECT
        COUNT(*) AS n,
        SUM(CASE WHEN student_id     IS NULL THEN 1 ELSE 0 END) AS n_student_id,
        SUM(CASE WHEN term_code       IS NULL THEN 1 ELSE 0 END) AS n_term_code,
        SUM(CASE WHEN term_gpa        IS NULL THEN 1 ELSE 0 END) AS n_term_gpa,
        SUM(CASE WHEN college         IS NULL THEN 1 ELSE 0 END) AS n_college
    FROM synthetic_enrollment
)
SELECT 'null_rate' AS check_name, col, null_rate,
       CASE WHEN null_rate > baseline * 2 THEN 'FAIL'
            WHEN null_rate > baseline     THEN 'WARN'
            ELSE 'PASS' END AS status
FROM nulls
CROSS JOIN LATERAL (
    VALUES
        ('student_id', n_student_id * 1.0 / n, 0.000),
        ('term_code',   n_term_code  * 1.0 / n, 0.000),
        ('term_gpa',    n_term_gpa   * 1.0 / n, 0.010),
        ('college',     n_college    * 1.0 / n, 0.005)
) AS v(col, null_rate, baseline);

/* ---- 2. Duplicate-key check: grain key (student_id, term_code) unique ---- */
SELECT 'duplicate_keys' AS check_name,
       'student_id+term_code' AS column_name,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status,
       COUNT(*) AS offending_rows
FROM (
    SELECT student_id, term_code
    FROM synthetic_enrollment
    GROUP BY student_id, term_code
    HAVING COUNT(*) > 1
) d;

/* ---- 3. Range check: GPA 0–4, credits 0–24 ---- */
SELECT 'range' AS check_name, 'term_gpa' AS column_name,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status,
       COUNT(*) AS offending_rows
FROM synthetic_enrollment
WHERE term_gpa IS NOT NULL AND (term_gpa < 0 OR term_gpa > 4.0);

SELECT 'range' AS check_name, 'credits_attempted' AS column_name,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status,
       COUNT(*) AS offending_rows
FROM synthetic_enrollment
WHERE credits_attempted IS NOT NULL AND (credits_attempted < 0 OR credits_attempted > 24);

/* ---- 4. Domain check: term_code must match expected pattern list ---- */
-- Unexpected term codes (typos like 'Falll 2024', or unmapped new codes)
SELECT 'domain' AS check_name, 'term_code' AS column_name,
       CASE WHEN COUNT(DISTINCT e.term_code) > 0 THEN 'FAIL' ELSE 'PASS' END AS status,
       COUNT(DISTINCT e.term_code) AS offending_values
FROM synthetic_enrollment e
LEFT JOIN synthetic_terms t ON t.term_code = e.term_code
WHERE e.term_code IS NOT NULL AND t.term_code IS NULL;

/* ---- 5. Referential integrity: every enrollment term exists in terms ---- */
SELECT 'referential_integrity' AS check_name, 'term_code' AS column_name,
       CASE WHEN COUNT(*) > 0 THEN 'FAIL' ELSE 'PASS' END AS status,
       COUNT(*) AS offending_rows
FROM synthetic_enrollment e
LEFT JOIN synthetic_terms t ON t.term_code = e.term_code
WHERE e.term_code IS NOT NULL AND t.term_code IS NULL;

/* ---- 6. Freshness check: latest load timestamp within 2 days ---- */
SELECT 'freshness' AS check_name, 'load_ts' AS column_name,
       CASE WHEN MAX(load_ts) < CURRENT_TIMESTAMP - INTERVAL '2 days'
            THEN 'FAIL' ELSE 'PASS' END AS status,
       MAX(load_ts) AS latest_load
FROM synthetic_enrollment;

/* ---- Sample of offending keys (capped, keys only — never full PII) ---- */
SELECT student_id, term_code
FROM synthetic_enrollment
WHERE term_gpa IS NOT NULL AND (term_gpa < 0 OR term_gpa > 4.0)
LIMIT 5;
