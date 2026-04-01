## Metadata

- **PR Type:** [feat | fix | docs | refactor | chore | test]
- **Component:** [cloud-functions | bigquery | dataform | cicd | infra | docs]
- **Function:** [ingest-fr24 | ingest-bts-csv | gemini-monitor | n/a]

## Summary

<!-- Briefly describe WHAT was changed and WHY. -->

## Related Issues

- Closes #

## Infrastructure Impact

<!-- Specify changes to GCP resources. Use "None" if no changes. -->

| Resource Type | Change Description |
| :--- | :--- |
| **Cloud Functions** | |
| **BigQuery** | |
| **GCS** | |
| **IAM** | |
| **CI/CD** | |

## Breaking Changes & Risk

- [ ] **Breaking Change?** (e.g., schema change, renamed column, moved GCS path)
- **Rollback Plan:** [Describe how to revert this change]

## Testing & Validation

- [ ] **Unit Tests:** All tests passed (`pytest tests/unit/`)
- [ ] **CI Checks:** PR checks workflow passed (lint, security, tests)
- [ ] **Integration:** Verified end-to-end (e.g., manual trigger via `curl`)
- [ ] **Data Landing:** Confirmed data in GCS/BigQuery
- [ ] **Logs:** No `ERROR` severity logs in Cloud Logging

## Standards & Quality Checks

- [ ] **Python:** Ruff lint passing, native Python 3.12 types used (no `List`/`Dict`/`Tuple`)
- [ ] **SQL:** Standard SQL only (no Legacy SQL)
- [ ] **Docs:** Updated `docs/architecture.md` or `docs/runbook.md` if behaviour changed
- [ ] **Secrets:** No hardcoded keys — Secret Manager used for all credentials

## Evidence (Optional)

<!-- Screenshots, logs, or BQ query results. -->

## Files Changed

<!-- Briefly list key files added or modified. -->
