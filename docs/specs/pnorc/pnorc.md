line based format data definitiobn lale, [🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC Specification

**Base current velocity message** with positional velocity measurements.

## Format

```
$PNORC,MMDDYY,HHMMSS,CellIndex,VelEast,VelNorth,VelUp*CHECKSUM
```

**Field Count**: 7 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number (1-based) |
| 4 | Velocity Component 1 | float | DECIMAL(8,4) | m/s | -10 to +10 | East (ENU) or X (XYZ) or Beam 1 |
| 5 | Velocity Component 2 | float | DECIMAL(8,4) | m/s | -10 to +10 | North (ENU) or Y (XYZ) or Beam 2 |
| 6 | Velocity Component 3 | float | DECIMAL(8,4) | m/s | -10 to +10 | Up (ENU) or Z (XYZ) or Beam 3 |

## Example Sentence

```
$PNORC,102115,090715,1,0.123,-0.456,0.012*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Cell Index: 1 (first measurement cell)
- Velocity 1: 0.123 m/s (eastward, if ENU)
- Velocity 2: -0.456 m/s (southward, if ENU)
- Velocity 3: 0.012 m/s (upward, if ENU)

## Validation Rules

1. **Date Format**: 6 digits, valid month/day
2. **Time Format**: 6 digits, valid hour/minute/second
3. **Cell Index**: Must be ≥ 1 and ≤ configured cell_count (from PNORI)
4. **Velocity Components**: Typically -10 to +10 m/s (instrument-dependent)

## Usage Notes

- **Multiple sentences**: One PNORC sentence per measurement cell
- **Cell order**: Cells typically sent sequentially (1, 2, 3, ...)
- **Timestamp**: All cells in a single profile share the same timestamp
- **Coordinate system**: Must reference PNO RI configuration to interpret components

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORI Configuration](../pnori/README.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
