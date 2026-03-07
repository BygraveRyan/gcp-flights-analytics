# SCD-2 Implementation Patterns

For all dimension tables (`dim_*`), follow these standards:

## Mandatory Columns
- **`is_current`**: `BOOL` - `TRUE` for the active version.
- **`effective_from`**: `DATE` - Record activation date.
- **`effective_to`**: `DATE` - Record expiration date (`NULL` for current).
- **`row_hash`**: `STRING` - `MD5()` of business attributes to detect changes.

## Surrogate Keys
- Always use `generate_surrogate_key()` macro for the primary key.
- Natural Key + Business Columns should form the base for the row hash.

## Macro Usage
- Use `scd2_merge()` for all dimension merges.
