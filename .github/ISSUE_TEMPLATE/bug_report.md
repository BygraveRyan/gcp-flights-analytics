---
name: Bug Report
about: Report a data pipeline failure, incorrect output, or infrastructure error
labels: bug
assignees: ''
---

## Summary

<!-- One sentence: what broke, where, and when. -->

## Component

- [ ] `fn-ingest-fr24`
- [ ] `fn-ingest-bts-csv`
- [ ] `fn-gemini-monitor`
- [ ] BigQuery / Dataform
- [ ] GCS storage
- [ ] CI/CD

## Expected Behaviour

<!-- What should have happened? -->

## Actual Behaviour

<!-- What happened instead? Include error messages or unexpected data. -->

## Steps to Reproduce

1.
2.
3.

## Evidence

<!-- Cloud Logging query, GCS path, BQ table snapshot, or screenshot. -->

```
# Paste relevant log output here
```

## Impact

- **Severity:** [P0 - pipeline down | P1 - data incorrect | P2 - degraded | P3 - minor]
- **Affected date range:** [e.g., 2026-03-28 to 2026-04-01]
- **Downstream impact:** [e.g., Looker Studio dashboard showing stale data]
