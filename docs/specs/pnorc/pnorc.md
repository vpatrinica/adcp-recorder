line based format data definitiobn lale, [🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC Specification

**Base current velocity message** with positional measurements.

## Format

```
$PNORC,Date,Time,Cell,Vel1,Vel2,Vel3,Vel4,Speed,Dir,AmpUnit,Amp1,Amp2,Amp3,Amp4,Corr1,Corr2,Corr3,Corr4*CHECKSUM
```

**Field Count**: 19 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC` |
| 1 | Date | str | CHAR(6) | - | YYMMDD | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| 4 | Vel 1 | float | DECIMAL(8,4) | m/s | -10 to +10 | East or X or Beam 1 |
| 5 | Vel 2 | float | DECIMAL(8,4) | m/s | -10 to +10 | North or Y or Beam 2 |
| 6 | Vel 3 | float | DECIMAL(8,4) | m/s | -10 to +10 | Up or Z or Beam 3 |
| 7 | Vel 4 | float | DECIMAL(8,4) | m/s | -10 to +10 | Vertical 2 or Beam 4 |
| 8 | Speed | float | DECIMAL(8,4) | m/s | 0-100 | Horizontal speed |
| 9 | Direction | float | DECIMAL(5,2) | degrees | 0-360 | Horizontal direction |
| 10| Amp Unit | str | CHAR(1) | - | C/D | C=Counts, D=dB |
| 11-14 | Amp 1-4 | int | SMALLINT | counts/dB | 0-255 | Amplitude per beam |
| 15-18 | Corr 1-4 | int | SMALLINT | % | 0-100 | Correlation per beam |

## Example Sentence

```
$PNORC,141112,081946,1,0.123,-0.456,0.012,0.001,0.472,164.9,C,80,82,79,81,98,99,97,98*XX
```

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
