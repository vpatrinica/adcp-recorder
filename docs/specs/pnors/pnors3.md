[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORS Family](README.md)

# PNORS3 Specification

**Compact sensor data format** with reduced fields.

## Format

```
$PNORS3,BV=Batt,SS=SndSpd,H=Head,PI=Pitch,R=Roll,P=Press,T=Temp*CS
```

**Field Count**: Variable (tags), but 7 value fields required.

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Range | Description |
|-----|-------|-------------|-------------|------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | - | Always `$PNORS3` |
| BV | Battery | float | DECIMAL(4,1) | volts | 0-30 | Battery voltage |
| SS | Sound Speed | float | DECIMAL(6,1) | m/s | 1400-1600 | Speed of sound |
| H | Heading | float | DECIMAL(5,1) | degrees | 0-360 | Compass heading |
| PI | Pitch | float | DECIMAL(4,1) | degrees | -90 to +90 | Instrument pitch |
| R | Roll | float | DECIMAL(5,1) | degrees | -180 to +180 | Instrument roll |
| P | Pressure | float | DECIMAL(7,3) | decibars | 0-20000 | Water pressure |
| T | Temperature | float | DECIMAL(5,2) | °C | -5 to +50 | Water temperature |

## Example Sentence

```
$PNORS3,BV=22.9,SS=1546.1,H=151.1,PI=-12.0,R=-5.2,P=705.669,T=24.96*7A
```

## Differences from PNORS

- **Format**: Tagged (TAG=VALUE)
- **Removed**: Date, time, error codes, status codes, analog inputs
- **Compact**: Essential sensor data only
- **Use**: Bandwidth-constrained applications

## Validation Rules

Same field validation as PNORS for included fields.

## Related Documents

- [PNORS Family Overview](README.md)
- [PNORS Base](pnors.md)

---

[⬆️ Back to PNORS Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
