# Code Sanitization Standards - flights-analytics-prod

## Python (Cloud Functions & PySpark)
- **Style**: PEP 8.
- **Formatting**: Always use `black`.
- **Imports**: Always use `isort`.
- **Type Hints**: Mandatory for all function signatures.
- **Logging**: Mandatory `logger` instantiation at module level.

## SQL (BigQuery & dbt)
- **Style**: Use `sqlfluff`.
- **Keywords**: UPPERCASE (e.g., `SELECT`, `FROM`).
- **Identifiers**: lowercase (e.g., `my_column`).
- **Functions**: UPPERCASE (e.g., `SUM()`).
- **Aliasing**: Always use explicit `AS`.
- **Syntax**: Standard SQL only (Never Legacy SQL).
