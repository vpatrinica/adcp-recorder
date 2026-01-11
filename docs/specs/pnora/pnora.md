[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORA Specification

**Altitude/range data message** for distance to surface or bottom.

## Format

```
$PNORA,Date,Time,Pressure,Distance,Quality,Status,Pitch,Roll*CHECKSUM
```

**Field Count**: 9 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORA` |
| 1 | Date | str | CHAR(6) | - | YYMMDD | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| 4 | Distance | float | DECIMAL(7,3) | meters | 0-1000 | Vertical distance |
| 5 | Quality | int | INTEGER | - | - | Quality indicator/confidence |
| 6 | Status | str | CHAR(2) | - | - | 2 hex digits status |
| 7 | Pitch | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument pitch |
| 8 | Roll | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument roll |

## Example Sentence

```
$PNORA,141112,084201,10.123,5.678,95,01,1.2,-0.5*XX
```

## Validation Rules

1. Date/time validation
2. Distance: 0-1000m
3. Status: 2 hex digits
4. Pitch/Roll: -90 to +90 degrees

## Related Documents

- [All Specifications](README.md)

---

[📋 All Specs](README.md) | [🏠 Home](../README.md)
