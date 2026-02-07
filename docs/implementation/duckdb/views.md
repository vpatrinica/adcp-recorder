# DuckDB View Patterns

[🏠 Home](../../README.md) > [Implementation](../README.md) > DuckDB

Views and materialized views for data access and aggregation.

## Consolidating View Pattern

Views are used to join consolidated tables across families.

### Current Profile View (DF101/102)

```sql
CREATE OR REPLACE VIEW current_profile_12 AS
SELECT
    s.record_id AS sensor_id,
    s.data_format,
    s.received_at,
    s.measurement_date,
    s.measurement_time,
    s.heading, s.pitch, s.roll, s.pressure, s.temperature,
    c.cell_index, c.cell_distance, c.vel1, c.vel2, c.vel3, c.vel4
FROM pnors12 s
JOIN pnorc12 c
    ON s.measurement_date = c.measurement_date
    AND s.measurement_time = c.measurement_time
    AND s.data_format = c.data_format;
```

### Wave Measurement View

```sql
CREATE OR REPLACE VIEW wave_measurement AS
SELECT
    w.record_id,
    w.received_at,
    w.measurement_date,
    w.measurement_time,
    w.hm0, w.h3, w.h10, w.hmax,
    w.tm02, w.tp, w.tz,
    w.dir_tp, w.spr_tp, w.main_dir,
    e.energy_densities
FROM pnorw_data w
LEFT JOIN pnore_data e
    ON w.measurement_date = e.measurement_date
    AND w.measurement_time = e.measurement_time;
```

## Union Pattern

Used to present a unified interface for configuration across all formats:

```sql
CREATE VIEW vw_all_configurations AS
SELECT config_id, 'PNORI' as sentence_type, head_id, received_at FROM pnori
UNION ALL
SELECT config_id, CASE WHEN data_format = 101 THEN 'PNORI1' ELSE 'PNORI2' END, head_id, received_at FROM pnori12;
```

## Related Documents

- [Schema Patterns](schemas.md)
- [Functions](functions.md)

---

[⬆️ Back to Implementation](../README.md) | [🏠 Home](../../README.md)
