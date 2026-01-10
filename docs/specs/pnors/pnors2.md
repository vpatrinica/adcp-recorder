[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS2 Specification

**Tagged sensor data format** with TAG=VALUE pairs.

## Format

```
$PNORS2,DT=MMDDYY,TM=HHMMSS,ER=ErrorHex,ST=StatusHex,BT=Battery,SS=SoundSpeed,HD=Heading,PT=Pitch,RL=Roll,PR=Pressure,TP=Temperature,A1=Analog1,A2=Analog2*CHECKSUM
```

**Field Count**: 15 fields (including prefix)

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Description |
|-----|-------|-------------|-------------|-------------|
| DT | Date | str | CHAR(6) | MMDDYY format |
| TM | Time | str | CHAR(6) | HHMMSS format |
| ER | Error Code | str | CHAR(8) | 8-char hex |
| ST | Status Code | str | CHAR(8) | 8-char hex |
| BT | Battery | float | DECIMAL(4,1) | Voltage in volts |
| SS | Sound Speed | float | DECIMAL(6,1) | m/s |
| HD | Heading | float | DECIMAL(5,1) | degrees |
| PT | Pitch | float | DECIMAL(4,1) | degrees |
| RL | Roll | float | DECIMAL(5,1) | degrees |
| PR | Pressure | float | DECIMAL(7,3) | decibars |
| TP | Temperature | float | DECIMAL(5,2) | degrees Celsius |
| A1 | Analog Input 1 | int | SMALLINT | integer value |
| A2 | Analog Input 2 | int | SMALLINT | integer value |

## Example Sentence

```
$PNORS2,DT=102115,TM=090715,ER=00000000,ST=2A480000,BT=14.4,SS=1523.0,HD=275.9,PT=15.7,RL=2.3,PR=0.000,TP=22.45,A1=0,A2=0*XX
```

## Differences from PNORS

- **Format**: Tagged (TAG=VALUE) instead of positional
- **Order**: Field order not significant
- **Same**: Data content identical to PNORS

## Valid Tags

Required: `DT`, `TM`, `ER`, `ST`, `BT`, `SS`, `HD`, `PT`, `RL`, `PR`, `TP`, `A1`, `A2`

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
