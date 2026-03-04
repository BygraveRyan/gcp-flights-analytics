---
name: dbt-architect
description: Expert guidance for developing dbt models in the flights-analytics-prod project. Use when creating or modifying staging, intermediate, fact, or dimension models to ensure compliance with SCD-2 and configuration standards.
---

# dbt Architect Skill

This skill ensures all dbt models follow the `flights-analytics-prod` standards for SCD-2, naming, and BigQuery optimization.

## Core Workflows

### 1. Model Scaffolding
Every new model **MUST** start with a `{{ config(...) }}` block.
- **Reference**: Use [model-template.sql](assets/model-template.sql) as a starting point.
- **Materialization**: 
  - Staging (`stg_`): `view`
  - Intermediate (`int_`): `table`
  - Dimension (`dim_`): `incremental` (SCD-2)
  - Fact (`fct_`): `table` or `incremental` (Partitioned)

### 2. Standard References
Refer to these for specific implementation details:
- **Global Standards**: [global-standards.md](references/global-standards.md) (Naming, constants, SQL style)
- **SCD-2 Patterns**: [scd2-patterns.md](references/scd2-patterns.md) (Mandatory fields and macros)

### 3. BigQuery Best Practices
- **Partitioning**: Always use `partition_by` in `config()` for Fact tables (e.g., `flight_date`).
- **Clustering**: Always use `cluster_by` for common filter columns (e.g., `carrier_code`).
- **Standard SQL**: Never use Legacy SQL.

## Quality Standards
- PKs must use `generate_surrogate_key()`.
- SCD-2 fields (`is_current`, `effective_from`, `effective_to`, `row_hash`) are non-negotiable for `dim_*` tables.
- All identifiers must be `snake_case`.
