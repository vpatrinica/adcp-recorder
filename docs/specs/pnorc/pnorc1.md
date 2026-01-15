[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC1 Specification

**Positional current velocity data** (DF=101) with cell position, velocities, amplitudes, and correlations.

## Format

```nmea
$PNORC1,Date,Time,Cell,Dist,Vel1,Vel2,Vel3,Vel4,Amp1,Amp2,Amp3,Amp4,Corr1,Corr2,Corr3,Corr4*CS
```

**Field Count**: 17 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORC1" | - | Always `$PNORC1` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| 3 | Cell Number | int | SMALLINT | - | N | 1-999 | Measurement cell index |
| 4 | Cell Position | float | DECIMAL(5,1) | m | dd.d | 0-999 | Distance from transducer |
| 5-8 | Velocity 1-4 | float | DECIMAL(6,3) | m/s | dd.ddd | -99 to +99 | Velocity components |
| 9-12 | Amplitude 1-4 | float | DECIMAL(5,1) | dB | ddd.d | 0-999 | Beam amplitudes |
| 13-16 | Correlation 1-4 | int | TINYINT | % | N | 0-100 | Beam correlations |

> [!NOTE]
> Velocity tags depend on coordinate system: ENU (VE/VN/VU/VU2), XYZ (VX/VY/VZ/VZ2), or BEAM (V1/V2/V3/V4).

## Example Sentence

```nmea
$PNORC1,083013,132455,3,11.0,0.332,0.332,0.332,0.332,78.9,78.9,78.9,78.9,78,78,78,78*46
```

**Parsed**:

- Date: August 30, 2013 (MMDDYY = 083013)
- Time: 13:24:55
- Cell Number: 3, Cell Position: 11.0 m
- Velocities: 0.332, 0.332, 0.332, 0.332 m/s
- Amplitudes: 78.9, 78.9, 78.9, 78.9 dB
- Correlations: 78%, 78%, 78%, 78%

## Related Documents

- [PNORC2](pnorc2.md) - Same data, tagged format
- [PNORC Family Overview](README.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
