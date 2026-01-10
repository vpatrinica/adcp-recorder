[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORA Specification

**Altitude/range data message** measuring distance from instrument to surface or bottom.

## Format

```
$PNORA,MMDDYY,HHMMSS,AltitudeMethod,Distance,Quality*CHECKSUM
```

**Field Count**: 6 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORA` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Method | int | TINYINT | - | 0-2 | Altitude measurement method |
| 4 | Distance | float | DECIMAL(6,2) | meters | 0-1000 | Distance to surface or bottom |
| 5 | Quality | int | TINYINT | % | 0-100 | Measurement quality indicator |

## Altitude Methods

- **0**: Pressure-based altitude
- **1**: Acoustic Surface Tracking (AST)
- **2**: Acoustic Bottom Tracking (ABT)

## Example Sentence

```
$PNORA,102115,090715,1,15.50,95*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Method: 1 (AST - Surface Tracking)
- Distance: 15.50 m
- Quality: 95%

## Related Documents

- [All Specifications](README.md)

---

[📋 All Specs](README.md) | [🏠 Home](../README.md)
