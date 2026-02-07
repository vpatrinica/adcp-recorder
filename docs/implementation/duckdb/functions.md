# DuckDB Function Patterns

[🏠 Home](../../README.md) > [Implementation](../README.md) > DuckDB

User-defined functions and stored procedures.

## Macro Pattern

DuckDB supports SQL macros for reusable logic:

```sql
CREATE OR REPLACE MACRO validate_checksum(sentence) AS (
    CASE 
        WHEN sentence LIKE '%*__' THEN TRUE
        ELSE FALSE
    END
);
```

## Python UDF Pattern

Complex logic is implemented via Python functions registered with DuckDB:

```python
def hex_to_int(value: str) -> int:
    try:
        return int(value, 16)
    except ValueError:
        return 0

conn.create_function("hex_to_int", hex_to_int, [VARCHAR], INTEGER)
```

## Maintenance Pattern

Maintenance operations are performed via SQL commands executed through the Python driver:

```python
def cleanup_database(conn, days_to_keep: int):
    conn.execute(f"""
        DELETE FROM raw_lines
        WHERE received_at < current_timestamp - INTERVAL '{days_to_keep} days'
    """)
    conn.execute("CHECKPOINT; ANALYZE; VACUUM;")
```

## Related Documents

- [Schema Patterns](schemas.md)
- [Constraints](constraints.md)
- [Views](views.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
