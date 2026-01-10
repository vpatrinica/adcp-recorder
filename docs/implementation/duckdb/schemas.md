[🏠 Home](../../README.md) > [Implementation](../README.md) > DuckDB

# DuckDB Schema Patterns

Table definition patterns for NMEA message storage.

## Basic Table Pattern

```sql
CREATE TABLE message_type_table (
    -- Primary key
    record_id UUID PRIMARY KEY DEFAULT uuid(),
    
    -- Metadata
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    sentence_type VARCHAR(10) NOT NULL,
    
    -- Data fields
    field1 INTEGER NOT NULL,
    field2 DECIMAL(10,2) NOT NULL,
    field3 VARCHAR(50) NOT NULL,
    
    -- Validation
    checksum CHAR(2),
    checksum_valid BOOLEAN NOT NULL
);
```

## Type Mapping

| Python Type | DuckDB Type | Notes |
|-------------|-------------|-------|
| int | INTEGER / TINYINT / SMALLINT | Choose based on range |
| float | DECIMAL(p,s) / DOUBLE | DECIMAL for precision |
| str | VARCHAR(n) / TEXT | VARCHAR for bounded, TEXT for unbounded |
| datetime.date | DATE | Native date type |
| datetime.time | TIME | Native time type |
| datetime.datetime | TIMESTAMP | Native timestamp type |
| bool | BOOLEAN | True/False |
| Optional[T] | T (nullable) | NULL allowed by default |

## Constraint Patterns

```sql
CREATE TABLE sensor_data (
    -- Range constraints
    temperature DECIMAL(5,2) NOT NULL
        CHECK (temperature BETWEEN -5.0 AND 50.0),
    
    -- Enum constraints
    coord_system VARCHAR(10) NOT NULL
        CHECK (coord_system IN ('ENU', 'XYZ', 'BEAM')),
    
    -- Format constraints
    error_code CHAR(8) NOT NULL
        CHECK (error_code ~ '^[0-9A-Fa-f]{8}$'),
    
    -- Cross-field constraints
    CONSTRAINT valid_blanking CHECK (
        blanking_distance < cell_size * cell_count
    )
);
```

## Index Patterns

```sql
-- Time-based queries
CREATE INDEX idx_received_at ON table_name(received_at);

-- Type-based queries
CREATE INDEX idx_sentence_type ON table_name(sentence_type);

-- Identifier lookups
CREATE INDEX idx_head_id ON table_name(head_id);

-- Composite index for common queries
CREATE INDEX idx_type_time ON table_name(sentence_type, received_at);
```

## Partitioning Pattern

```sql
-- Monthly partitions for large datasets
CREATE TABLE raw_lines_2025_01 AS
SELECT * FROM raw_lines
WHERE received_at >= '2025-01-01' 
  AND received_at < '2025-02-01';

CREATE INDEX idx_lines_2025_01_time 
ON raw_lines_2025_01(received_at);
```

## Related Documents

- [Constraints](constraints.md)
- [Views](views.md)
- [Functions](functions.md)
- [DuckDB Integration](../../architecture/duckdb-integration.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
