[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORW Specification

**Wave data message** with wave height, period, and direction measurements.

## Format

```
$PNORW,Date,Time,Basis,Method,Hm0,H3,H10,Hmax,Tm02,Tp,Tz,DirTp,SprTp,MainDir,UI,MeanPress,NoDetect,BadDetect,NSurfSpeed,NSurfDir,ErrorCode*CS
```

**Field Count**: 22 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORW" | - | Always `$PNORW` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | hhmmss | - | Measurement time |
| 3 | Spectrum Basis | int | TINYINT | - | N | 0,1,3 | 0=Pressure, 1=Velocity, 3=AST |
| 4 | Processing Method | int | TINYINT | - | N | 1-4 | 1=PUV, 2=SUV, 3=MLM, 4=MLMST |
| 5 | Hm0 | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Significant wave height |
| 6 | H3 | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Mean height of largest 1/3 |
| 7 | H10 | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Mean height of largest 1/10 |
| 8 | Hmax | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Max wave height |
| 9 | Tm02 | float | DECIMAL(5,2) | s | dd.dd | 0-99.99 | Mean wave period |
| 10 | Tp | float | DECIMAL(5,2) | s | dd.dd | 0-99.99 | Peak wave period |
| 11 | Tz | float | DECIMAL(5,2) | s | dd.dd | 0-99.99 | Zero-crossing period |
| 12 | DirTp | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Peak direction |
| 13 | SprTp | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Directional spread at peak |
| 14 | MainDir | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Mean direction |
| 15 | UI | float | DECIMAL(5,2) | - | dd.dd | 0-99.99 | Unidirectivity index |
| 16 | Mean Pressure | float | DECIMAL(5,2) | dBar | dd.dd | 0-99.99 | Mean pressure |
| 17 | Num No Detects | int | INTEGER | - | N | ≥0 | Count of no detects |
| 18 | Num Bad Detects | int | INTEGER | - | N | ≥0 | Count of bad detects |
| 19 | Near Surf Speed | float | DECIMAL(5,2) | m/s | dd.dd | 0-99.99 | Current speed near surface |
| 20 | Near Surf Dir | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Current dir near surface |
| 21 | Error Code | str | CHAR(4) | - | hhhh | - | Wave error code (4 hex) |

> [!NOTE]
> Values of -9, -9.00, -999, etc. indicate **invalid data** per manufacturer specification.

## Example Sentence

```
$PNORW,102115,090715,0,1,2.50,2.6,3.0,4.10,7.5,8.5,7.2,285.0,20.0,280.0,0.8,12.5,0,0,0.5,120.0,0000*XX
```

**Parsed**:

- Date: 10/21/15, Time: 09:07:15
- Hm0: 2.50m, Hmax: 4.10m
- Tp: 8.5s, Tm02: 7.5s
- DirTp: 285.0°, MainDir: 280.0°
- Mean Pressure: 12.5 dBar

## Related Documents

- [PNORWD - Wave Directional Data](../pnorwd/pnorwd.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
