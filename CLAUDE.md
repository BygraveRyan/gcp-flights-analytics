# CLAUDE.md — flights-analytics-prod

Primary coding agent instructions for Claude Code.

## Project Context

GCP data pipeline: BTS + FR24 → Cloud Functions → GCS → BigQuery (Dataform) → Looker Studio.
Project ID: `flights-analytics-prod` | Region: `europe-west2` | Python 3.12

Read `docs/architecture.md` before starting any task. It is the source of truth.

## Hard Prohibitions

- **NEVER** run `gcloud`, `bq`, `gsutil` commands — propose them for the human to run
- **NEVER** push to `main` or `dev` branches
- **NEVER** hardcode secrets or API keys — use Secret Manager
- **NEVER** use Legacy SQL — Standard SQL only
- **NEVER** use `from typing import List, Dict, Tuple, Optional` — use native Python 3.12 types
- **NEVER** use `functions_framework.Request` as type hint — use `request: Any` (import Any from typing)
- **NEVER** commit directly to `main` or `dev`

## Code Patterns

### Cloud Functions (Gen2, Python 3.12)

```python
from typing import Any
import functions_framework
import logging

logging.basicConfig(level=logging.INFO)
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
- All DDL targets `flights-analytics-prod` project
- Datasets: `flights_staging`, `flights_dw`
- Partition by date columns, cluster by high-cardinality filter columns
- Surrogate keys: MD5 hash of natural key fields

### Dataform SQLX

- All files in `bigquery/dataform/definitions/`
- Use `${ref("table_name")}` for dependencies — never hardcode dataset paths
- Staging: `config { type: "view" }`
- Fact/dim loads: `config { type: "incremental" }` or `config { type: "operations" }` for MERGEs

## Git Workflow

All work on `feat/short-description` branches.

```bash
git add <specific files>        # never git add -A or git add .
git commit -m "type(scope): description"
# Then propose: gh pr create --base dev ...
# Human reviews and merges
```

Conventional commit scopes: `cloud-functions`, `bigquery`, `dataform`, `cicd`, `docs`, `tests`

## Infrastructure Commands (propose, never run)

```bash
# Deploy Cloud Function
gcloud functions deploy fn-ingest-fr24 \
  --gen2 --runtime=python312 --region=europe-west2 \
  --source=cloud_functions/ingest_fr24 \
  --entry-point=ingest_fr24 --trigger-http \
  --no-allow-unauthenticated \
  --timeout=120s --memory=256Mi \
  --min-instances=0

# Run BigQuery DDL
bq query --use_legacy_sql=false < bigquery/ddl/<file>.sql
```

## Architecture Quick Reference

| Layer | What | Where |
| --- | --- | --- |
| Ingestion | Cloud Functions Gen2 | `cloud_functions/` |
| Raw storage | GCS audit bucket | `flights-bronze-flights-analytics-prod` |
| Staging | BigQuery `flights_staging` | `raw_bts_flights`, `raw_fr24_positions` |
| Transformation | Dataform SQLX | `bigquery/dataform/` |
| Warehouse | BigQuery `flights_dw` | Star schema (fact + dims) |
| Reporting | Materialized Views | `bigquery/materialized_views/` |
| Orchestration | Cloud Scheduler | 06:00 UTC daily |
| AI monitoring | Gemini 2.5 Pro via google-genai SDK | `cloud_functions/gemini_monitor/` |
