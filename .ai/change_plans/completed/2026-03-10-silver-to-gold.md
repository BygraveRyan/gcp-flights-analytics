# Change Plan: Phase 4 — PySpark Silver → Gold

- Date: 2026-03-10
- Request: Implement Phase 4 of the flights-analytics-prod pipeline.
- Status: complete — Checkpoint at Phase 4

## Why

This change implements the Gold layer of the lakehouse architecture, providing business-level aggregates and enriched flight data for downstream analytics and reporting.

## Current State

- Phase 3 (Bronze → Silver) is complete with `spark_jobs/bronze_to_silver.py`.
- Silver Parquet data exists in `gs://flights-silver-flights-analytics-prod/bts`.
- Phase 4 is described in `docs/architecture.md` but no implementation files exist yet.

## Proposed Changes

- Implement `spark_jobs/silver_to_gold.py`:
    - Read Silver BTS Parquet.
    - Enrich with computed columns (total delay, delay category, surrogate keys).
    - Compute route-level daily aggregates (total flights, avg delays, on-time rate).
    - Write Gold Parquet to `gs://flights-gold-flights-analytics-prod/fact_flights` and `gs://flights-gold-flights-analytics-prod/mart_route_performance`.
- Implement unit tests for `silver_to_gold.py` in `tests/unit/test_silver_to_gold.py`.
- Update `docs/architecture_summary.md` and `docs/changelog.md` to reflect Phase 4 completion.

## Expected Touch Points

- `spark_jobs/silver_to_gold.py` (New)
- `tests/unit/test_silver_to_gold.py` (New)
- `docs/architecture_summary.md` (Update)
- `docs/changelog.md` (Update)

## Risks

- Data quality in Silver might affect Gold aggregations.
- Partitioning strategy needs to be consistent with BigQuery external table expectations.

## Verification

- `pytest tests/unit/test_silver_to_gold.py`
- Manual inspection of generated Parquet schema (if possible in local/dev environment).
- **Final Note:** Verified Phase 4 logic via unit tests on March 10, 2026. Documentation and mirrors synchronized on March 11, 2026.

## Docs And Mirror Impact

- Architecture summary: yes
- Changelog: yes
- Obsidian mirror: yes
