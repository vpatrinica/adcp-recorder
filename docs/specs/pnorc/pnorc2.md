[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC2 Specification

**Tagged current velocity format** with TAG=VALUE pairs.

## Format

```
$PNORC2,DT=MMDDYY,TM=HHMMSS,CI=CellIndex,VE=VelE,VN=VelN,VU=VelU*CHECKSUM
```

**Field Count**: 7 fields (including prefix)

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Range | Description |
|-----|-------|-------------|-------------|------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC2` |
| DT | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| TM | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| CI | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| VE | Velocity East/X | float | DECIMAL(8,4) | m/s | -10 to +10 | First velocity component |
| VN | Velocity North/Y | float | DECIMAL(8,4) | m/s | -10 to +10 | Second velocity component |
| VU | Velocity Up/Z | float | DECIMAL(8,4) | m/s | -10 to +10 | Third velocity component |

## Example Sentence

```
$PNORC2,DT=102115,TM=090715,CI=1,VE=0.123,VN=-0.456,VU=0.012*XX
```

**Parsed**:
- Date (DT): October 21, 2015
- Time (TM): 09:07:15
- Cell Index (CI): 1
- Velocity East (VE): 0.123 m/s
- Velocity North (VN): -0.456 m/s
- Velocity Up (VU): 0.012 m/s

## Valid Tags

Required tags: `DT`, `TM`, `CI`, `VE`, `VN`, `VU`

## Differences from PNORC

- **Format**: Tagged (TAG=VALUE) instead of positional
- **Order**: Field order not significant
- **Same**: Data content identical to PNORC

## Validation Rules

1. All required tags must be present
2. Tag format: exactly one '=' per field
3. Field values same as PNORC

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC Base](pnorc.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
