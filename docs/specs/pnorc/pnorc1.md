[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC1 Specification

**Current velocity variant 1** with extended format.

## Format

```
$PNORC1,Date,Time,Cell,Dist,Vel1,Vel2,Vel3,Vel4,Amp1,Amp2,Amp3,Amp4,Corr1,Corr2,Corr3,Corr4*CS
```

**Field Count**: 17 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC1` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| 4 | Cell Position | float | DECIMAL(8,3) | m | 0-1000 | Distance from transducer |
| 5 | Velocity 1 | float | DECIMAL(8,4) | m/s | -10 to +10 | Vel component 1 (East/X/Beam1) |
| 6 | Velocity 2 | float | DECIMAL(8,4) | m/s | -10 to +10 | Vel component 2 (North/Y/Beam2) |
| 7 | Velocity 3 | float | DECIMAL(8,4) | m/s | -10 to +10 | Vel component 3 (Up/Z1/Beam3) |
| 8 | Velocity 4 | float | DECIMAL(8,4) | m/s | -10 to +10 | Vel component 4 (Up2/Z2/Beam4) |
| 9 | Amplitude 1 | float | DECIMAL(6,2) | dB | 0-255 | Amplitude Beam 1 |
| 10 | Amplitude 2 | float | DECIMAL(6,2) | dB | 0-255 | Amplitude Beam 2 |
| 11 | Amplitude 3 | float | DECIMAL(6,2) | dB | 0-255 | Amplitude Beam 3 |
| 12 | Amplitude 4 | float | DECIMAL(6,2) | dB | 0-255 | Amplitude Beam 4 |
| 13 | Correlation 1 | int | TINYINT | % | 0-100 | Correlation Beam 1 |
| 14 | Correlation 2 | int | TINYINT | % | 0-100 | Correlation Beam 2 |
| 15 | Correlation 3 | int | TINYINT | % | 0-100 | Correlation Beam 3 |
| 16 | Correlation 4 | int | TINYINT | % | 0-100 | Correlation Beam 4 |

## Example Sentence

```
$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78,78,78,78*46
```

**Parsed**:
- Date: August 30, 2013
- Time: 13:24:55
- Cell: 3
- Distance: 11.0 m
- Velocities: 0.332, 0.332, 0.332, 0.332 m/s
- Amplitudes: 78.9, 78.9, 78.9, 78.9 dB
- Correlations: 78%, 78%, 78%, 78%

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
