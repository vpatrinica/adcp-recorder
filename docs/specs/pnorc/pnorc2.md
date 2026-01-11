[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC2 Specification

**Tagged current velocity format** with TAG=VALUE pairs.

## Format

```
$PNORC2,DATE=MMDDYY,TIME=HHMMSS,CN=Cell,CP=Dist,VE=Vel1,VN=Vel2,VU=Vel3,VU2=Vel4,A1=Amp1,A2=Amp2,A3=Amp3,A4=Amp4,C1=Corr1,C2=Corr2,C3=Corr3,C4=Corr4*CS
```

**Field Count**: Variable (tags), but 16 value fields required.

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Range | Description |
|-----|-------|-------------|-------------|------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | - | Always `$PNORC2` |
| DATE | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| TIME | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| CN | Cell Index | int | SMALLINT | - | 1-1000 | Measurement cell number |
| CP | Cell Position | float | DECIMAL(8,3) | m | 0-1000 | Distance from transducer |
| VE/V1/VX | Velocity 1 | float | DECIMAL(8,4) | m/s | -10 to +10 | East/Beam1/X velocity |
| VN/V2/VY | Velocity 2 | float | DECIMAL(8,4) | m/s | -10 to +10 | North/Beam2/Y velocity |
| VU/V3/VZ | Velocity 3 | float | DECIMAL(8,4) | m/s | -10 to +10 | Up/Beam3/Z1 velocity |
| VU2/V4/VZ2 | Velocity 4 | float | DECIMAL(8,4) | m/s | -10 to +10 | Up2/Beam4/Z2 velocity |
| A1-A4 | Amplitudes | float | DECIMAL(6,2) | dB | 0-255 | Beam Amplitudes |
| C1-C4 | Correlations | int | TINYINT | % | 0-100 | Beam Correlations |

## Example Sentence

```
$PNORC2,DATE=083013,TIME=132455,CN=3,CP=11.0,VE=0.332,VN=0.332,VU=0.332,VU2=0.332,A1=78.9,A2=78.9,A3=78.9,A4=78.9,C1=78,C2=78,C3=78,C4=78*49
```

**Parsed**:
- Date: August 30, 2013
- Time: 13:24:55
- Cell Index (CN): 3
- Distance (CP): 11.0 m
- Velocities: 0.332, 0.332, 0.332, 0.332 m/s
- Amplitudes: 78.9 dB each
- Correlations: 78% each

## Valid Tags

Required tags: `DATE`, `TIME`, `CN`, `CP`, plus velocity (e.g. `VE,VN,VU,VU2`), amplitude `A1-A4`, and correlation `C1-C4` tags.

## Differences from PNORC

- **Format**: Tagged (TAG=VALUE) instead of positional
- **Order**: Field order not significant
- **Same**: Data content identical to PNORC

## Validation Rules

1. All required tags must be present
2. Tag format: exactly one '=' per field
3. Field values same as PNORC

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC Base](pnorc.md)

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
