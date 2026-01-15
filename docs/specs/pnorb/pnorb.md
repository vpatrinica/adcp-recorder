[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORB Specification

**Wave band parameters message** (DF=501) containing wave statistics for specific frequency bands.

## Format

```nmea
$PNORB,Date,Time,Basis,Method,FreqLow,FreqHigh,Hm0,Tm02,Tp,DirTp,SprTp,MainDir,ErrorCode*CS
```

**Field Count**: 14 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORB" | - | Always `$PNORB` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | - | Measurement date |
| 2 | Time | str | CHAR(6) | - | hhmmss | - | Measurement time |
| 3 | Spectrum Basis | int | TINYINT | - | N | 0,1,3 | 0=Pressure, 1=Velocity, 3=AST |
| 4 | Processing Method | int | TINYINT | - | N | 1-4 | 1=PUV, 2=SUV, 3=MLM, 4=MLMST |
| 5 | Freq Low | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Band start frequency |
| 6 | Freq High | float | DECIMAL(4,2) | Hz | d.dd | 0-9.99 | Band end frequency |
| 7 | Hm0 | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Significant wave height in band |
| 8 | Tm02 | float | DECIMAL(5,2) | s | dd.dd | 0-99.99 | Mean period in band |
| 9 | Tp | float | DECIMAL(5,2) | s | dd.dd | 0-99.99 | Peak period in band |
| 10 | DirTp | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Peak direction in band |
| 11 | SprTp | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Directional spread in band |
| 12 | MainDir | float | DECIMAL(6,2) | deg | ddd.dd | 0-360 | Mean direction in band |
| 13 | Wave Error Code | str | CHAR(4) | - | hhhh | - | Error code (hex) |

## Processing Methods

| Value | Method | Description |
|-------|--------|-------------|
| 1 | PUV | Pressure-velocity method |
| 2 | SUV | Subsurface velocity method |
| 3 | MLM | Maximum likelihood method |
| 4 | MLMST | MLM with smoothing |

## Example Sentence

```nmea
$PNORB,120720,093150,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*67
```

**Parsed**:

- Date: July 20, 2012 (MMDDYY = 120720)
- Time: 09:31:50
- Spectrum Basis: 1 (Velocity)
- Processing Method: 4 (MLMST)
- Band: 0.02-0.20 Hz
- Hm0: 0.27 m in band
- Tm02: 7.54 s, Tp: 12.00 s
- DirTp: 82.42°, SprTp: 75.46°, MainDir: 82.10°
- Error Code: 0000 (no errors)

## Related Documents

- [PNORW - Wave Parameters](../pnorw/pnorw.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
