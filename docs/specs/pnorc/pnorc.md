[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC Specification

**Current velocity data** (DF=100) with velocities, speed, direction, amplitudes, and correlations.

## Format

```nmea
$PNORC,Date,Time,Cell,Vel1,Vel2,Vel3,Vel4,Speed,Dir,AmpUnit,Amp1,Amp2,Amp3,Amp4,Corr1,Corr2,Corr3,Corr4*CHECKSUM
```

**Field Count**: 19 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORC" | - | Always `$PNORC` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| 3 | Cell Number | int | SMALLINT | - | N | 1-999 | Measurement cell index |
| 4 | Velocity 1 | float | DECIMAL(6,2) | m/s | dd.dd | -99 to +99 | Beam1/X/East |
| 5 | Velocity 2 | float | DECIMAL(6,2) | m/s | dd.dd | -99 to +99 | Beam2/Y/North |
| 6 | Velocity 3 | float | DECIMAL(6,2) | m/s | dd.dd | -99 to +99 | Beam3/Z1/Up1 |
| 7 | Velocity 4 | float | DECIMAL(6,2) | m/s | dd.dd | -99 to +99 | Beam4/Z2/Up2 (3-beam: empty) |
| 8 | Speed | float | DECIMAL(6,2) | m/s | dd.dd | 0-99 | Horizontal speed |
| 9 | Direction | float | DECIMAL(5,1) | deg | ddd.d | 0-360 | Horizontal direction |
| 10 | Amplitude Unit | str | CHAR(1) | - | C or D | - | C=Counts, D=dB |
| 11-14 | Amplitude 1-4 | int | SMALLINT | - | N | 0-255 | Amplitude per beam |
| 15-18 | Correlation 1-4 | int | SMALLINT | % | N | 0-100 | Correlation per beam |

> [!NOTE]
> Velocity 4, Amplitude 4, and Correlation 4 are not relevant for 3-beam systems (will be empty).

## Example Sentence

```nmea
$PNORC,102115,090715,4,0.56,-0.80,-1.99,-1.33,0.98,305.2,C,80,88,67,78,13,17,10,18*22
```

**Parsed**:

- Date: October 21, 2015 (MMDDYY = 102115), Time: 09:07:15
- Cell: 4
- Velocities: 0.56, -0.80, -1.99, -1.33 m/s
- Speed: 0.98 m/s, Direction: 305.2°
- Amplitude Unit: C (Counts), Amplitudes: 80, 88, 67, 78
- Correlations: 13%, 17%, 10%, 18%

## Related Documents

- [PNORC1](pnorc1.md) - Same data, simplified format
- [PNORC2](pnorc2.md) - Same data, tagged format
- [PNORC Family Overview](README.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
