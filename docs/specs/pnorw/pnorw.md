[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORW Specification

**Wave data message** with wave height, period, and direction measurements.

## Format

```
$PNORW,Date,Time,Basis,Method,Hm0,H3,H10,Hmax,Tm02,Tp,Tz,DirTp,SprTp,MainDir,UI,MeanPress,NoDetect,BadDetect,NSurfSpeed,NSurfDir,ErrorCode*CS
```

**Field Count**: 22 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORW` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Spectrum Basis | int | TINYINT | - | 0-3 | Spectrum type |
| 4 | Processing Method | int | TINYINT | - | 1-4 | Proc method |
| 5 | Hm0 | float | DECIMAL(6,3) | m | 0-100 | Significant wave height |
| 6 | H3 | float | DECIMAL(6,3) | m | 0-100 | Mean height of largest 1/3 |
| 7 | H10 | float | DECIMAL(6,3) | m | 0-100 | Mean height of largest 1/10 |
| 8 | Hmax | float | DECIMAL(6,3) | m | 0-100 | Max wave height |
| 9 | Tm02 | float | DECIMAL(6,3) | s | 0-100 | Mean wave period |
| 10 | Tp | float | DECIMAL(6,3) | s | 0-100 | Peak wave period |
| 11 | Tz | float | DECIMAL(6,3) | s | 0-100 | Zero-crossing period |
| 12 | DirTp | float | DECIMAL(6,1) | deg | 0-360 | Peak direction |
| 13 | SprTp | float | DECIMAL(6,1) | deg | 0-360 | Directional spread |
| 14 | MainDir | float | DECIMAL(6,1) | deg | 0-360 | Mean direction |
| 15 | UI | float | DECIMAL(6,3) | - | - | Unidirectivity index |
| 16 | Mean Pressure | float | DECIMAL(7,3) | dBar | - | Mean pressure |
| 17 | Num No Detects | int | INTEGER | - | - | Count of no detects |
| 18 | Num Bad Detects | int | INTEGER | - | - | Count of bad detects |
| 19 | Near Surf Speed | float | DECIMAL(6,3) | m/s | - | Current speed near surface |
| 20 | Near Surf Dir | float | DECIMAL(6,1) | deg | 0-360 | Current dir near surface |
| 21 | Error Code | str | CHAR(4) | - | - | Wave error code |

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
