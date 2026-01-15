[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS2 Specification

**Tagged sensor data with uncertainty** (DF=102) including standard deviation fields.

## Format

```nmea
$PNORS2,DATE=Date,TIME=Time,EC=Err,SC=Stat,BV=Batt,SS=SndSpd,HSD=HeadSD,H=Head,PI=Pitch,PISD=PitchSD,R=Roll,RSD=RollSD,P=Press,PSD=PressSD,T=Temp*CS
```

**Field Count**: Variable (tags), 16 fields typically

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|-----|-------|-------------|-------------|------|--------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | "$PNORS2" | - | Always `$PNORS2` |
| DATE | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| TIME | Time | str | CHAR(6) | - | HHMMSS | - | Measurement time |
| EC | Error Code | int | INTEGER | - | N | 0+ | Error identifier |
| SC | Status Code | str | CHAR(8) | - | hhhhhhhh | - | Status bitmask (hex) |
| BV | Battery | float | DECIMAL(4,1) | V | dd.d | 0-99 | Battery voltage |
| SS | Sound Speed | float | DECIMAL(6,1) | m/s | dddd.d | 1400-2000 | Speed of sound |
| HSD | Heading StdDev | float | DECIMAL(5,2) | deg | dd.dd | 0-99 | Heading std dev |
| H | Heading | float | DECIMAL(5,1) | deg | ddd.d | 0-360 | Compass heading |
| PI | Pitch | float | DECIMAL(4,1) | deg | dd.d | -90 to +90 | Instrument pitch |
| PISD | Pitch StdDev | float | DECIMAL(5,2) | deg | dd.dd | 0-99 | Pitch std dev |
| R | Roll | float | DECIMAL(4,1) | deg | dd.d | -90 to +90 | Instrument roll |
| RSD | Roll StdDev | float | DECIMAL(5,2) | deg | dd.dd | 0-99 | Roll std dev |
| P | Pressure | float | DECIMAL(7,3) | dBar | ddd.ddd | 0-999 | Water pressure |
| PSD | Pressure StdDev | float | DECIMAL(5,2) | dBar | dd.dd | 0-99 | Pressure std dev |
| T | Temperature | float | DECIMAL(5,2) | °C | dd.dd | -5 to +50 | Water temperature |

## Example Sentence

```nmea
$PNORS2,DATE=083013,TIME=132455,EC=0,SC=34000034,BV=22.9,SS=1500.0,HSD=0.02,H=123.4,PI=45.6,PISD=0.02,R=23.4,RSD=0.02,P=123.456,PSD=0.02,T=24.56*3F
```

**Parsed**:

- Date: August 30, 2013 (MMDDYY = 083013), Time: 13:24:55
- Error Code (EC): 0, Status (SC): 34000034
- Battery (BV): 22.9 V, Sound Speed (SS): 1500.0 m/s
- Heading (H): 123.4° (±0.02° HSD)
- Pitch (PI): 45.6° (±0.02° PISD), Roll (R): 23.4° (±0.02° RSD)
- Pressure (P): 123.456 dBar (±0.02 PSD), Temperature (T): 24.56°C

## Related Documents

- [PNORS1](pnors1.md) - Same data, positional format
- [PNORS Family Overview](README.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
