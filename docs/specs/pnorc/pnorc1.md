[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC1 Specification

**Current velocity variant 1** with extended format.

## Format

```
$PNORC1,MMDDYY,HHMMSS,CellIndex,VelE,VelN,VelU,Correlation1,Correlation2,Correlation3*CHECKSUM
```

**Field Count**: 10 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC1` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| 4 | Velocity East/X | float | DECIMAL(8,4) | m/s | -10 to +10 | First velocity component |
| 5 | Velocity North/Y | float | DECIMAL(8,4) | m/s | -10 to +10 | Second velocity component |
| 6 | Velocity Up/Z | float | DECIMAL(8,4) | m/s | -10 to +10 | Third velocity component |
| 7 | Correlation 1 | int | TINYINT | % | 0-100 | Correlation for beam/component 1 |
| 8 | Correlation 2 | int | TINYINT | % | 0-100 | Correlation for beam/component 2 |
| 9 | Correlation 3 | int | TINYINT | % | 0-100 | Correlation for beam/component 3 |

## Example Sentence

```
$PNORC1,102115,090715,1,0.123,-0.456,0.012,95,92,88*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Cell: 1
- Velocities: 0.123, -0.456, 0.012 m/s
- Correlations: 95%, 92%, 88%

## Differences from PNORC

- **Added**: Three correlation values for quality assessment
- **Same**: Velocity components and cell indexing

## Validation Rules

1. Date/time format validation
2. Cell index: 1 to configured cell_count
3. Velocities: typically -10 to +10 m/s
4. Correlations: 0-100%

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC Base](pnorc.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
