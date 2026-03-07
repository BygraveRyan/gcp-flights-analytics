# GEMINI.md - Project `flights-analytics-prod`

<project_identity>

- Project ID: `flights-analytics-prod`
- Region: `europe-west2`
- Python Version: `3.12`
- Key Libraries: PySpark 3.5, dbt Core 1.8.x, Airflow 2.10.3 (Composer 3), google-cloud-storage 2.18.2, functions-framework 3.8.1
</project_identity>

<critical_constraints>
The Agent MUST adhere to these absolute negative constraints at all times:

- NEVER use placeholder comments like `# TODO` or `...`. Implement logic completely.
- NEVER use Legacy SQL. Always write BigQuery Standard SQL (`standard#`).
- NEVER use `from typing import Tuple, Dict`. Always use native Python 3.12 lowercase types: `dict[str, Any]`, `list[int]`, `tuple[str, int]`.
- NEVER use `functions_framework.Request` as a type hint; use `Any` for HTTP request parameters.
- NEVER assume or guess file locations. The repository structure is dynamic.
- NEVER use `docs` as a git commit scope. Use specific areas (e.g., `gemini`, `architecture`, `readme`).
</critical_constraints>

<agent_directives>

### 1. File System & Context

- Always use the GitHub MCP or available file system tools to read the current directory state before attempting to edit, create, or delete files.
- Use the Gemini CLI for generating/editing code, multi-file scaffolding, and explaining errors.

### 2. Code Generation Rules

- Always include the standard `logging` module in all Python files (`cloud_functions/` and `spark_jobs/`), logging key operations (I/O, API calls) and exceptions (`exc_info=True`).
- Always add appropriate `try...except` error handling in Python for I/O and API calls, raising exceptions only for unrecoverable errors.
- All dbt models must include a `{{ config(...) }}` block at the top specifying `materialized`, `tags`, and `labels`.
- Treat PySpark DataFrames as immutable. Create new DataFrames for each transformation step.
- Repartition PySpark data before writing to GCS (`.repartition("partition_key")`).

### 3. Git & Commits

- Commit Message Format: `type(scope): description`
- Valid Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`
- Valid Scopes: `cloud-functions`, `spark`, `bigquery`, `dbt`, `composer`, `dataplex`, `cicd`, `infra`, `architecture`
- PR Title Format: `feat: phase X — description`
</agent_directives>

<runbook_synchronization_protocol>

### Trigger

When the Agent detects the User describing or performing terminal-based infrastructure tasks (e.g., `gcloud` commands, secret management, IAM configs, troubleshooting sequences).

### Action Pipeline

1. **Context Retrieval**: Use the `github_mcp` tool to `read_file` at path `docs/runbook.md` to get the live state.
2. **Schema Extraction**: Analyze the live `docs/runbook.md` for header formats, content blocks, and "lessons learned" patterns.
3. **Drafting Phase**: Generate a new entry draft within the conversation using exact terminal syntax and the identified schema.
4. **Verification Loop (Mandatory)**: Present the draft in a Markdown code block. Wait for explicit user confirmation before using `github_mcp` to write or push changes to `docs/runbook.md`.
</runbook_synchronization_protocol>

<user_protocols>
The User will execute the following directly in the terminal (not through the Agent):

- All `gcloud` commands
- All `bq` CLI commands
- All `git` commands
- All `curl` tests
- Any command modifying GCP infrastructure
- Post-merge synchronization: `git checkout dev`, `git pull origin main`, `git push origin dev`
</user_protocols>

---

## 🏗️ ARCHITECTURE & DATA FLOW

<architecture_summary>

### GCS Lakehouse Zones

- **Bronze Zone (Raw)**: `gs://flights-bronze-flights-analytics-prod` (TTL: 30 days) - Raw CSV/JSON.
- **Silver Zone (Validated)**: `gs://flights-silver-flights-analytics-prod` (TTL: 90 days) - Cleaned, schema-enforced Parquet.
- **Gold Zone (Business)**: `gs://flights-gold-flights-analytics-prod` (TTL: Indefinite) - Aggregates/features for analytics.

### BigQuery Datasets

- `flights_raw`: External tables pointing to GCS Silver zone.
- `flights_staging`: dbt staging models (views).
- `flights_dw`: Core data warehouse with facts (SCD-2) and dimensions.
- `flights_marts`: Reporting-layer tables for Looker Studio.

### Data Flow Pipeline

1. Sources -> `cloud_functions/fn-ingest-*` -> Bronze GCS
2. Bronze -> `bronze_to_silver.py` (Dataproc) -> Silver GCS
3. Silver -> `silver_to_gold.py` (Dataproc) -> Gold GCS
4. Gold -> `flights_raw` (External Tables)
5. `flights_raw` -> dbt Models -> `flights_dw` & `flights_marts`
</architecture_summary>

<data_contracts>

### Delay Categories (`delay_category` column)

- SEVERE_DELAY: `arr_delay_minutes > 60`
- MODERATE_DELAY: `15 < arr_delay_minutes <= 60`
- MINOR_DELAY: `0 < arr_delay_minutes <= 15`
- ON_TIME: `arr_delay_minutes <= 0`
- CANCELLED: `is_cancelled = TRUE`
- DIVERTED: `is_diverted = TRUE`

### SCD-2 Fields (`dim_*` tables)

- `is_current` (BOOL): TRUE if active record.
- `effective_from` (DATE): Date version became active.
- `effective_to` (DATE): Date version expired (NULL for current).
- `row_hash` (STRING): MD5 of business attribute columns.

### BigQuery Partitioning & Clustering

- `fact_flights`: PARTITION BY `flight_date`, CLUSTER BY `carrier_code`, `origin_airport`.
- `mart_delay_summary`: PARTITION BY `summary_date`, CLUSTER BY `carrier_code`.
</data_contracts>

---

## 📋 CONVENTIONS & CONFIGURATION

<naming_conventions>

- **Tables**: `fct_` (Fact), `dim_` (Dimension), `stg_` (Staging views), `int_` (Intermediate tables), `mart_` (Reporting marts).
- **Files**: `snake_case.py`, `snake_case.sql`.
- **Variables/Columns**: `snake_case` for all Python/SQL variables and DataFrame columns.
</naming_conventions>

<style_guides>

- **Python**: PEP 8. Format with `black` and `isort`. Use type hints (`def func(param: str) -> int:`). Use `get_spark_session()` for PySpark.
- **SQL**: Use explicit `AS` for aliases. Cross-dataset queries must use `project-id.dataset.table`. Format using `sqlfluff` (Keywords/Functions: UPPERCASE, Identifiers: lowercase).
- **dbt**: Generate primary/surrogate keys using `MD5()` of natural key + business columns via `generate_surrogate_key()`. Use `scd2_merge()` for SCD-2 dimensions.
</style_guides>

<iam_roles>

- **Pipeline Runner SA** (`flights-pipeline-sa@...`): `bigquery.dataEditor`, `bigquery.jobUser`, `storage.objectAdmin`, `dataproc.editor`, `dataplex.editor`, `aiplatform.user`, `composer.worker`, `cloudfunctions.invoker`.
- **Dataproc SA** (`flights-dataproc-sa@...`): `bigquery.dataEditor`, `bigquery.jobUser`, `storage.objectAdmin`, `dataproc.worker`.
- **CI/CD SA** (`flights-cicd-sa@...`): `bigquery.dataEditor`, `bigquery.jobUser`, `storage.objectAdmin`, `dataproc.editor`, `cloudfunctions.developer`, `iam.serviceAccountTokenCreator`.
</iam_roles>
