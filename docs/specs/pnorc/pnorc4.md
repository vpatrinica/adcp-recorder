[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC4 Specification

**Complete current velocity format** with all quality metrics.

## Format

```
$PNORC4,MMDDYY,HHMMSS,CellIndex,VelE,VelN,VelU,Corr1,Corr2,Corr3,Amp1,Amp2,Amp3,Amp4*CHECKSUM
```

**Field Count**: 14 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC4` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| 4 | Velocity East/X | float | DECIMAL(8,4) | m/s | -10 to +10 | First velocity component |
| 5 | Velocity North/Y | float | DECIMAL(8,4) | m/s | -10 to +10 | Second velocity component |
| 6 | Velocity Up/Z | float | DECIMAL(8,4) | m/s | -10 to +10 | Third velocity component |
| 7 | Correlation 1 | int | TINYINT | % | 0-100 | Correlation beam/component 1 |
| 8 | Correlation 2 | int | TINYINT | % | 0-100 | Correlation beam/component 2 |
| 9 | Correlation 3 | int | TINYINT | % | 0-100 | Correlation beam/component 3 |
| 10 | Amplitude Beam 1 | int | TINYINT | counts | 0-255 | Echo amplitude beam 1 |
| 11 | Amplitude Beam 2 | int | TINYINT | counts | 0-255 | Echo amplitude beam 2 |
| 12 | Amplitude Beam 3 | int | TINYINT | counts | 0-255 | Echo amplitude beam 3 |
| 13 | Amplitude Beam 4 | int | TINYINT | counts | 0-255 | Echo amplitude beam 4 |

## Example Sentence

```
$PNORC4,102115,090715,1,0.123,-0.456,0.012,95,92,88,145,152,148,150*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Cell: 1
- Velocities: 0.123, -0.456, 0.012 m/s
- Correlations: 95%, 92%, 88%
- Amplitudes: 145, 152, 148, 150 counts

## Differences from Other PNORC Variants

- **Most Complete**: Includes both correlation and amplitude data
- **Combines**: Features from PNORC1 (correlation) and PNORC3 (amplitude)
- **Use**: Full quality assessment and data validation

## Validation Rules

1. Date/time format validation
2. Cell index: 1 to configured cell_count
3. Velocities: typically -10 to +10 m/s
4. Correlations: 0-100%
5. Amplitudes: 0-255 counts

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC Base](pnorc.md)
- [PNORC1](pnorc1.md) - Correlation data
- [PNORC3](pnorc3.md) - Amplitude data

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
