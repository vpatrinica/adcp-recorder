[🏠 Home](../../README.md) > [Implementation](../README.md) > DuckDB

# DuckDB Constraint Patterns

CHECK constraints and cross-field validation patterns.

## Domain Constraints

```sql
-- Numeric ranges
temperature DECIMAL(5,2) CHECK (temperature BETWEEN -5.0 AND 50.0),
pressure DECIMAL(7,3) CHECK (pressure BETWEEN 0.0 AND 20000.0),
heading DECIMAL(5,1) CHECK (heading >= 0.0 AND heading < 360.0),

-- String enumerations
coord_system VARCHAR(10) CHECK (coord_system IN ('ENU', 'XYZ', 'BEAM')),
instrument_type VARCHAR(20) CHECK (instrument_type IN ('AQUADOPP', 'AQUADOPP_PROFILER', 'SIGNATURE')),

-- Format validation (regex)
error_code CHAR(8) CHECK (error_code ~ '^[0-9A-Fa-f]{8}$'),
date_str CHAR(6) CHECK (date_str ~ '^\d{6}$'),

-- Positive values
cell_count SMALLINT CHECK (cell_count > 0),
beam_count TINYINT CHECK (beam_count > 0 AND beam_count <= 4)
```

## Cross-Field Constraints

```sql
-- Named constraints for clarity
CONSTRAINT valid_signature_config CHECK (
    NOT (instrument_type_code = 4 AND beam_count != 4)
),

CONSTRAINT valid_aquadopp_beams CHECK (
    NOT (instrument_type_code IN (0, 2) AND beam_count NOT IN (1, 2, 3))
),

CONSTRAINT valid_blanking_ratio CHECK (
    blanking_distance < cell_size * cell_count
),

CONSTRAINT valid_coord_mapping CHECK (
    (coord_system_name = 'ENU' AND coord_system_code = 0) OR
    (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
    (coord_system_name = 'BEAM' AND coord_system_code = 2)
)
```

## Temporal Constraints

```sql
-- Date fields must be valid
CONSTRAINT valid_date CHECK (
    CAST(SUBSTR(date_str, 1, 2) AS INTEGER) BETWEEN 1 AND 12 AND
    CAST(SUBSTR(date_str, 3, 2) AS INTEGER) BETWEEN 1 AND 31
),

-- Time fields must be valid
CONSTRAINT valid_time CHECK (
    CAST(SUBSTR(time_str, 1, 2) AS INTEGER) BETWEEN 0 AND 23 AND
    CAST(SUBSTR(time_str, 3, 2) AS INTEGER) BETWEEN 0 AND 59 AND
    CAST(SUBSTR(time_str, 5, 2) AS INTEGER) BETWEEN 0 AND 59
),

-- Timestamp ordering
CONSTRAINT valid_timestamp_order CHECK (
    received_at <= current_timestamp
)
```

## Conditional Constraints

```sql
-- Only validate if field is not NULL
CONSTRAINT valid_analog_range CHECK (
    analog_input_1 IS NULL OR (analog_input_1 >= 0 AND analog_input_1 <= 65535)
),

-- Different rules based on type
CONSTRAINT type_specific_validation CHECK (
    CASE instrument_type_code
        WHEN 4 THEN beam_count = 4  -- Signature
        WHEN 0 THEN beam_count IN (1,2,3)  -- Aquadopp
        WHEN 2 THEN beam_count IN (1,2,3)  -- Aquadopp Profiler
        ELSE TRUE
    END
)
```

## Related Documents

- [Schema Patterns](schemas.md)
- [Data Validation](../../nmea/validation.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
