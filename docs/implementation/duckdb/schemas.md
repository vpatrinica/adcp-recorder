# DuckDB Schema Patterns

[🏠 Home](../../README.md) > [Implementation](../README.md) > DuckDB

Table definition patterns for NMEA message storage.

## Basic Table Pattern

```sql
CREATE TABLE message_type_table (
    -- Primary key (using BIGINT and sequences for better performance)
    record_id BIGINT PRIMARY KEY,
    
    -- Metadata
    received_at TIMESTAMP DEFAULT current_timestamp,
    original_sentence TEXT NOT NULL,
    
    -- Data fields (using DECIMAL for precision)
    field1 INTEGER NOT NULL,
    field2 DECIMAL(10,2) NOT NULL,
    
    -- Validation
    checksum CHAR(2)
);
```

### Sequence Pattern

Each table family uses a dedicated sequence for primary key generation:

```sql
CREATE SEQUENCE IF NOT EXISTS table_name_seq START 1;
-- Usage: nextval('table_name_seq')
```

## Type Mapping

| Python Type | DuckDB Type | Notes |
| :--- | :--- | :--- |
| int (ID) | BIGINT | Used for primary keys with sequences |
| int | INTEGER / TINYINT / SMALLINT | Choose based on range |
| float | DECIMAL(p,s) / DOUBLE | DECIMAL for precision |
| str | VARCHAR(n) / TEXT | VARCHAR for bounded, TEXT for unbounded |
| datetime.date | CHAR(6) | Stored as 'YYMMDD' string for NMEA compatibility |
| datetime.time | CHAR(6) | Stored as 'HHMMSS' string for NMEA compatibility |
| datetime.datetime | TIMESTAMP | Native timestamp type for `received_at` |
| bool | BOOLEAN | True/False |
| list / dict | JSON | Stored using DuckDB's JSON extension |
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

## Consolidation Pattern

Tables are consolidated into families with a discriminator field (e.g., `data_format`) to simplify management:

```sql
CREATE TABLE pnors12 (
    record_id BIGINT PRIMARY KEY,
    data_format TINYINT NOT NULL CHECK (data_format IN (101, 102)),
    -- ... common fields
);
```

## Related Documents

- [Constraints](constraints.md)
- [Views](views.md)
- [Functions](functions.md)
- [DuckDB Integration](../../architecture/duckdb-integration.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
