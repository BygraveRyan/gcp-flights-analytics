# Global Standards - flights-analytics-prod

## Project Constants
- **Project ID**: `flights-analytics-prod`
- **Region**: `europe-west2`

## Naming Conventions
- **Case**: Always use `snake_case` for columns, variables, and file names.
- **Table Prefixes**:
    - `fct_`: Fact tables
    - `dim_`: Dimension tables
    - `stg_`: Staging models
    - `int_`: Intermediate models
    - `mart_`: Reporting marts

## SQL Style
- **Keywords**: UPPERCASE (e.g., `SELECT`, `FROM`)
- **Identifiers**: lowercase (e.g., `my_column`)
- **Functions**: UPPERCASE (e.g., `COUNT()`)
- **Aliasing**: Always use explicit `AS`.
- **Reference**: Follow BigQuery Standard SQL only.
