# Privacy Rules

These patterns are designed so data-quality work never becomes a privacy incident.

1. **Synthetic by default.** Every example, screenshot, and sample in this repo uses invented data. Real extracts stay inside the secured warehouse — they are never committed here.
2. **Keys only in output.** Check reports sample up to 5 *key values* (e.g. `student_id`), never full rows. A null-rate report does not need anyone's GPA attached.
3. **No PII in code or comments.** No names, no real IDs, no real institution names — not even "anonymized" ones. If a value could identify someone, it doesn't belong in the repo.
4. **Warehouse-first for real data.** The SQL checks exist so validation can run where the data lives, with results (counts, rates) exported — not row-level extracts pulled to a laptop.
5. **Aggregates are not automatically safe.** Small-n cells (e.g. one student in a program × demographic slice) can re-identify. Suppress or roll up cells below your institution's threshold (commonly n < 5) before publishing.
