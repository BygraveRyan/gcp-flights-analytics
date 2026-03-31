# GCP Flights Analytics — GitHub Governance
Version: 1.0

---

## 1. Purpose

This document defines the branching, commit, and PR rules for the `gcp-flights-analytics` repository. The goal is to ensure every change is traceable, reversible, and cost-accountable — consistent with the architectural principles of the project.

---

## 2. Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production only — never commit directly |
| `dev` | Integration branch — all feature PRs target here |
| `feat/<description>` | All new work (e.g. `feat/bigquery-ddl`, `feat/dataform-setup`) |
| `fix/<description>` | Bug fixes |
| `refactor/<description>` | Architectural changes with no new functionality |
| `docs/<description>` | Documentation-only changes |
| `chore/<description>` | Maintenance, dependency updates, cleanup |

### Rules

- Direct commits to `main` or `dev` are prohibited
- All changes go through a PR targeting `dev`
- `dev` → `main` merges are human-only, via PR

---

## 3. Commit Protocol

Format: `<type>(<scope>): <short summary>`

**Types:** `feat` · `fix` · `docs` · `refactor` · `chore` · `test`

**Scopes:**

| Scope | When to use |
|---|---|
| `cloud-functions` | Changes inside `cloud_functions/` |
| `bigquery` | DDL, materialized views |
| `dataform` | Anything inside `bigquery/dataform/` |
| `cicd` | `.github/workflows/` |
| `infra` | GCP infrastructure changes |
| `docs` | `docs/`, `README.md`, `CLAUDE.md`, `GEMINI.md` |

Each commit must follow the **Why / How / Impact** structure defined in `.github/commit_template.md`.

---

## 4. Pull Request Requirements

All PRs must:
- Use `.github/pull_request_template.md`
- Target `dev` (never `main` directly)
- Pass all CI checks (`pr_checks.yml`) before merge
- Include Infrastructure Impact assessment for any GCP resource changes
- Include a rollback plan for breaking changes

### Merge Criteria

A PR may only be merged if:
- CI passes (lint, tests, sqlfluff)
- Infrastructure Impact table is complete
- No secrets or hardcoded credentials present
- Breaking changes have a documented rollback plan

---

## 5. What to Commit

```
cloud_functions/        ✅ Source code for ingestion functions
bigquery/               ✅ DDL, Dataform SQLX, materialized views
.github/                ✅ Governance, templates, workflows
tests/                  ✅ Unit tests
docs/                   ✅ Architecture docs, runbook, changelog
CLAUDE.md               ✅ Agent governance
GEMINI.md               ✅ Agent governance
README.md               ✅ Project documentation
```

## 6. What NOT to Commit

```
.env                    ❌ Secrets
service-account*.json   ❌ GCP credentials
*_key.json              ❌ Any key files
__pycache__/            ❌ Python cache
```

---

## 7. Risk Classification

| Risk | Examples | Requirement |
|---|---|---|
| LOW | docs, comments, tests | Standard PR |
| MEDIUM | Cloud Function logic, Dataform SQLX | PR + CI pass |
| HIGH | DDL schema changes, IAM, CI/CD pipelines | PR + rollback plan documented |

High-risk changes must document how to revert in the PR description.

---

## 8. AI Agent Governance

Claude Code and Gemini CLI operate under explicit permission boundaries defined in `CLAUDE.md` and `GEMINI.md`. Neither agent may:
- Push to `main` or `dev`
- Merge any PR
- Run `gcloud`, `bq`, or `gsutil` commands
- Hardcode secrets or project IDs

All agent-proposed infrastructure commands must be reviewed and executed by the human.
