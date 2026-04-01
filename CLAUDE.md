# CLAUDE.md — flights-analytics-prod

Primary coding agent instructions for Claude Code.
Project: `flights-analytics-prod` | Region: `europe-west2` | Python 3.12

---

## Pipeline at a Glance

| Layer | Technology | Location |
| --- | --- | --- |
| Ingestion | Cloud Functions Gen2 (Python 3.12) | `cloud_functions/` |
| Raw storage | GCS single audit bucket | `flights-bronze-flights-analytics-prod` |
| Staging | BigQuery `flights_staging` | `raw_bts_flights`, `raw_fr24_positions` |
| Transformation | Dataform SQLX | `bigquery/dataform/definitions/` |
| Warehouse | BigQuery `flights_dw` | Star schema — fact + dims |
| Reporting | BigQuery Materialized Views | `bigquery/materialized_views/` |
| Orchestration | Cloud Scheduler | 06:00 UTC daily |
| AI monitoring | Gemini 2.5 Pro (`google-genai` SDK) | `cloud_functions/gemini_monitor/` |
| CI/CD | GitHub Actions | `.github/workflows/` |

---

## Context Loading

Load context based on task type — do not blanket-read all docs on every task:

| Task type | Read before starting |
| --- | --- |
| New feature / new file | `docs/architecture.md` + `docs/changelog.md` |
| Infrastructure change | `docs/runbook.md` |
| Bug fix / test / docs update | CLAUDE.md is sufficient |
| Anything touching schema or Dataform | `docs/architecture.md` sections 5–6 |

---

## Hard Prohibitions

- **NEVER** run `gcloud`, `bq`, or `gsutil` — propose commands for the human to run
- **NEVER** commit, push, or merge directly to `main` — `main` is human-only
- **NEVER** hardcode secrets or API keys — use Secret Manager
- **NEVER** use Legacy SQL — Standard SQL only
- **NEVER** use `from typing import List, Dict, Tuple, Optional` — native Python 3.12 types only
- **NEVER** use `functions_framework.Request` as a type hint — use `request: Any`

---

## When to Stop and Ask

Pause and confirm with the human before proceeding if:

- The task requires a schema change (adding/removing columns, changing types)
- You are about to delete or overwrite existing business logic
- The approach requires a `gcloud`/`bq` command with destructive or irreversible effect
- The task scope is ambiguous and two reasonable interpretations exist

---

## Code Patterns

### Cloud Functions (Gen2, Python 3.12)

```python
from typing import Any
import functions_framework
import logging

logger = logging.getLogger(__name__)

@functions_framework.http
def function_name(request: Any) -> tuple[dict, int]:
    request_json = request.get_json(silent=True) or {}
    try:
        ...
        return {"status": "success", ...}, 200
    except SpecificException as e:
        logger.error(f"...: {e}")
        return {"status": "error", "message": str(e)}, 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500
```

### BigQuery SQL

- Standard SQL only — no Legacy SQL
- DDL targets `flights-analytics-prod`; datasets: `flights_staging`, `flights_dw`
- Partition by date columns; cluster by high-cardinality filter columns
- Surrogate keys: MD5 hash of natural key fields

### Dataform SQLX

- Files in `bigquery/dataform/definitions/`
- Use `${ref("table_name")}` for dependencies — never hardcode dataset paths
- Staging views: `config { type: "view" }`
- Fact/dim loads: `config { type: "incremental" }` or `config { type: "operations" }` for MERGEs

---

## Git Workflow

All work on `feat/short-description` branches off `dev`.

```bash
git add <specific files>           # never git add -A or git add .
git commit -m "type(scope): description"
# Create and merge PR into dev yourself:
# gh pr create --base dev
# gh pr merge --merge
# main is off limits — never push, merge, or create PRs targeting main
```

Commit scopes: `cloud-functions`, `bigquery`, `dataform`, `cicd`, `docs`, `tests`

---

## Documentation Rules

Every PR that changes code **must** include a docs commit in the same branch. No follow-ups.

| What changed | Update required |
| --- | --- |
| Any code change | `docs/changelog.md` — date, what, why, files affected |
| Infrastructure added/removed/modified | `docs/runbook.md` — new state, commands proposed, lessons |
| Repo structure, stack, or Dataform files | `docs/architecture.md` — sections 3, 6, or 12 as applicable |

`docs/changelog.md` format:

```markdown
## YYYY-MM-DD
### <phase or feature name>
- Change: ...
- Impact: ...
- Areas: ...
```
