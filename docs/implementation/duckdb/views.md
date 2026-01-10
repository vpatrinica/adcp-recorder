[🏠 Home](../../README.md) > [Implementation](../README.md) > DuckDB

# DuckDB View Patterns

Views and materialized views for data access and aggregation.

## Normalized View Pattern

```sql
-- Hide implementation details, present clean interface
CREATE VIEW vw_sensor_data_normalized AS
SELECT 
    record_id,
    received_at,
    measurement_datetime,
    
    -- Mapped enumerations
    CASE instrument_type_code
        WHEN 0 THEN 'AQUADOPP'
        WHEN 2 THEN 'AQUADOPP_PROFILER'
        WHEN 4 THEN 'SIGNATURE'
    END AS instrument_type,
    
    CASE coord_system_code
        WHEN 0 THEN 'ENU'
        WHEN 1 THEN 'XYZ'
        WHEN 2 THEN 'BEAM'
    END AS coord_system,
    
    -- Physical values
    temperature,
    pressure,
    heading,
    pitch,
    roll
FROM sensor_data
WHERE checksum_valid = TRUE;
```

## Statistics View Pattern

```sql
CREATE VIEW vw_instrument_statistics AS
SELECT 
    instrument_type_name,
    head_id,
    COUNT(*) as total_records,
    MIN(received_at) as first_seen,
    MAX(received_at) as last_seen,
    AVG(temperature) as avg_temperature,
    MIN(pressure) as min_pressure,
    MAX(pressure) as max_pressure
FROM sensor_data
WHERE checksum_valid = TRUE
GROUP BY instrument_type_name, head_id;
```

## Materialized View Pattern

```sql
-- Pre-compute expensive aggregations
CREATE MATERIALIZED VIEW mv_daily_statistics AS
SELECT 
    DATE_TRUNC('day', received_at) as measurement_date,
    sentence_type,
    COUNT(*) as record_count,
    COUNT(DISTINCT head_id) as instrument_count,
    SUM(CASE WHEN checksum_valid THEN 1 ELSE 0 END) as valid_count,
    SUM(CASE WHEN NOT checksum_valid THEN 1 ELSE 0 END) as invalid_count
FROM raw_lines
GROUP BY DATE_TRUNC('day', received_at), sentence_type;

-- Refresh periodically
CREATE OR REPLACE PROCEDURE refresh_daily_stats()
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_daily_statistics;
END;
$$;
```

## Union View Pattern

```sql
-- Combine multiple message types
CREATE VIEW vw_all_configurations AS
SELECT config_id, sentence_type, instrument_type_name, head_id, received_at
FROM pnori_configurations
UNION ALL
SELECT config_id, sentence_type, instrument_type_name, head_id, received_at
FROM pnori1_configurations
UNION ALL
SELECT config_id, sentence_type, instrument_type_name, head_id, received_at
FROM pnori2_configurations;
```

## Related Documents

- [Schema Patterns](schemas.md)
- [Functions](functions.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
