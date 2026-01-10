[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC3 Specification

**Extended precision current velocity format** with additional beam data.

## Format

```
$PNORC3,MMDDYY,HHMMSS,CellIndex,VelE,VelN,VelU,Amplitude1,Amplitude2,Amplitude3,Amplitude4*CHECKSUM
```

**Field Count**: 11 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC3` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| 4 | Velocity East/X | float | DECIMAL(8,4) | m/s | -10 to +10 | First velocity component |
| 5 | Velocity North/Y | float | DECIMAL(8,4) | m/s | -10 to +10 | Second velocity component |
| 6 | Velocity Up/Z | float | DECIMAL(8,4) | m/s | -10 to +10 | Third velocity component |
| 7 | Amplitude Beam 1 | int | TINYINT | counts | 0-255 | Echo amplitude beam 1 |
| 8 | Amplitude Beam 2 | int | TINYINT | counts | 0-255 | Echo amplitude beam 2 |
| 9 | Amplitude Beam 3 | int | TINYINT | counts | 0-255 | Echo amplitude beam 3 |
| 10 | Amplitude Beam 4 | int | TINYINT | counts | 0-255 | Echo amplitude beam 4 (if present) |

## Example Sentence

```
$PNORC3,102115,090715,1,0.123,-0.456,0.012,145,152,148,150*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Cell: 1
- Velocities: 0.123, -0.456, 0.012 m/s
- Amplitudes: 145, 152, 148, 150 counts

## Differences from PNORC

- **Added**: Four beam amplitude values
- **Use**: Enhanced quality assessment with echo strength
- **Same**: Velocity components

## Validation Rules

1. Date/time format validation
2. Cell index: 1 to configured cell_count
3. Velocities: typically -10 to +10 m/s
4. Amplitudes: 0-255 counts

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC Base](pnorc.md)
- [PNORE Echo Intensity](../pnore/pnore.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
