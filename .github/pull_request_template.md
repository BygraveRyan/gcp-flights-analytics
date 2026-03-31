<!-- 
  V.A.N.T.i.S. Pull Request Template (GCP Edition)
  Follow the "Why, How, Impact" framework to tell the story of this change.
-->

## 📖 The Story

### WHY - What problem are we solving?
<!-- Explain the friction or limitation in the current architecture. -->


### HOW - What did we actually change?
<!-- Detail the technical implementation. -->


### IMPACT - What is the result?
<!-- Explain how the system is better now. -->

---

## 📋 Metadata
- **PR Type:** [feat | fix | docs | refactor | chore | test]
- **Component:** [cloud-functions | bigquery | dataform | cicd | infra | docs]
- **Phase:** [e.g., Phase 1, Phase 2]

## 🚀 Summary
<!-- Briefly describe WHAT was changed and WHY. -->

## 🔗 Related Issues
- Closes #

## 🏗️ Infrastructure Impact
<!-- Specify changes to GCP resources. Use "None" if no changes. -->

| Resource Type | Change Description |
| :--- | :--- |
| **BigQuery** | |
| **GCS** | |
| **Dataplex** | |
| **IAM** | |
| **CI/CD** | |

## ⚠️ Breaking Changes & Risk
- [ ] **Breaking Change?** (e.g., schema change, renamed column, moved GCS path)
- **Rollback Plan:** [Describe how to revert this change]

## 🧪 Testing & Validation
- [ ] **Unit Tests:** All tests passed (`pytest`)
- [ ] **Integration:** Verified end-to-step (e.g., `curl`, manual trigger)
- [ ] **Data Landing:** Confirmed data in GCS/BigQuery
- [ ] **Logs:** No `ERROR` severity logs in Cloud Logging

## ✅ Standards & Quality Checks
- [ ] **Python:** PEP 8 (ruff/black/isort)
- [ ] **SQL:** Standard SQL (sqlfluff)
- [ ] **Docs:** Updated `GEMINI.md`, `docs/architecture.md`, or `docs/runbook.md`
- [ ] **Types:** Native Python 3.12 type hints used (no `Tuple`/`Dict`)

## 📊 Evidence (Optional)
<!-- Screenshots, logs, or BQ query results. -->

## 📁 Files Changed
<!-- Briefly list key files added or modified. -->

<!-- 
AGENT GUIDANCE:
1. Populate 'Metadata' using the PR title and current milestone.
2. For 'Infrastructure Impact', analyze the git diff for DDL, YAML configs, or IAM updates.
3. Ensure 'Summary' explains the business value or technical necessity.
4. Mark checkboxes [x] only if you have verified the specific standard or test.
-->

<!-- AGENT_INSTRUCTIONS: When populating the 'Infrastructure Impact' table, inspect the git diff for: 1. BigQuery: .sql files or dbt models. 2. GCS: New buckets or path logic changes. 3. Dataplex: dq_rules updates. 4. IAM: service account changes. 5. CI/CD: workflow updates. If no changes exist for a category, write 'None'. -->
