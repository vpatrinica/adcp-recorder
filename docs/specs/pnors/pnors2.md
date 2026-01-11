[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS2 Specification

**Tagged sensor data format** with TAG=VALUE pairs.

## Format

```
$PNORS2,DATE=Date,TIME=Time,EC=Err,SC=Stat,BV=Batt,SS=SndSpd,HSD=HeadSD,H=Head,PI=Pitch,PISD=PitchSD,R=Roll,RSD=RollSD,P=Press,PSD=PressSD,T=Temp*CS
```

**Field Count**: Variable (tags), but 15 value fields required.

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Description |
|-----|-------|-------------|-------------|-------------|
| DATE | Date | str | CHAR(6) | MMDDYY format |
| TIME | Time | str | CHAR(6) | HHMMSS format |
| EC | Error Code | int | INTEGER | Error identifier |
| SC | Status Code | str | CHAR(8) | 8-char hex |
| BV | Battery | float | DECIMAL(4,1) | Voltage in volts |
| SS | Sound Speed | float | DECIMAL(6,1) | m/s |
| HSD | Heading StdDev | float | DECIMAL(5,1) | degrees |
| H | Heading | float | DECIMAL(5,1) | degrees |
| PI | Pitch | float | DECIMAL(4,1) | degrees |
| PISD | Pitch StdDev | float | DECIMAL(4,1) | degrees |
| R | Roll | float | DECIMAL(5,1) | degrees |
| RSD | Roll StdDev | float | DECIMAL(5,1) | degrees |
| P | Pressure | float | DECIMAL(7,3) | decibars |
| PSD | Pressure StdDev | float | DECIMAL(7,3) | decibars |
| T | Temperature | float | DECIMAL(5,2) | degrees Celsius |

## Example Sentence

```
$PNORS2,DATE=083013,TIME=132455,EC=0,SC=34000034,BV=22.9,SS=1500.0,HSD=0.02,H=123.4,PI=45.6,PISD=0.02,R=23.4,RSD=0.02,P=123.456,PSD=0.02,T=24.56*3F
```

## Differences from PNORS

- **Format**: Tagged (TAG=VALUE) instead of positional
- **Order**: Field order not significant
- **Same**: Data content identical to PNORS

## Valid Tags

Required: `DATE`, `TIME`, `EC`, `SC`, `BV`, `SS`, `HSD`, `H`, `PI`, `PISD`, `R`, `RSD`, `P`, `PSD`, `T`

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
