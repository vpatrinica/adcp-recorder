[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC2 Specification

**Tagged current velocity data** (DF=102) with cell position, velocities, amplitudes, and correlations.

## Format

```nmea
$PNORC2,DATE=MMDDYY,TIME=HHMMSS,CN=Cell,CP=Dist,VE=Vel1,VN=Vel2,VU=Vel3,VU2=Vel4,A1=Amp1,A2=Amp2,A3=Amp3,A4=Amp4,C1=Corr1,C2=Corr2,C3=Corr3,C4=Corr4*CS
```

**Field Count**: Variable (tags), 17 fields typically

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|-----|-------|-------------|-------------|------|--------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | "$PNORC2" | - | Always `$PNORC2` |
| DATE | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| TIME | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| CN | Cell Number | int | SMALLINT | - | N | 1-999 | Measurement cell index |
| CP | Cell Position | float | DECIMAL(5,1) | m | dd.d | 0-999 | Distance from transducer |
| VE/VN/VU/VU2 | Velocity (ENU) | float | DECIMAL(6,3) | m/s | dd.ddd | -99 to +99 | East/North/Up velocities |
| VX/VY/VZ/VZ2 | Velocity (XYZ) | float | DECIMAL(6,3) | m/s | dd.ddd | -99 to +99 | X/Y/Z velocities |
| V1/V2/V3/V4 | Velocity (BEAM) | float | DECIMAL(6,3) | m/s | dd.ddd | -99 to +99 | Beam velocities |
| A1-A4 | Amplitude 1-4 | float | DECIMAL(5,1) | dB | ddd.d | 0-999 | Beam amplitudes |
| C1-C4 | Correlation 1-4 | int | TINYINT | % | N | 0-100 | Beam correlations |

> [!NOTE]
> Velocity tags depend on coordinate system: ENU (VE/VN/VU/VU2), XYZ (VX/VY/VZ/VZ2), or BEAM (V1/V2/V3/V4).

## Example Sentence

```nmea
$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,V1=0.332,V2=0.332,V3=-0.332,V4=-0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49
```

**Parsed**:

- Date: August 30, 2013 (MMDDYY = 083013)
- Time: 13:24:55
- Cell Number (CN): 3, Cell Position (CP): 11.0 m
- Velocities: 0.332, 0.332, -0.332, -0.332 m/s
- Amplitudes: 78.9 dB each
- Correlations: 78% each

## Related Documents

- [PNORC1](pnorc1.md) - Same data, positional format
- [PNORC Family Overview](README.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
