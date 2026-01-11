[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORB Specification

**Wave Band parameters message** (DF=501).
 
 ## Format
 
 ```
 $PNORB,Date,Time,Basis,Method,FreqLow,FreqHigh,Hm0,Tm02,Tp,DirTp,SprTp,MainDir,ErrorCode*CS
 ```

**Field Count**: 14 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORB` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Spectrum Basis | int | TINYINT | - | 0-3 | Spectrum type |
| 4 | Processing Method | int | TINYINT | - | 1-4 | Proc method |
| 5 | Freq Low | float | DECIMAL(4,2) | Hz | 0-10 | Band valid start freq |
| 6 | Freq High | float | DECIMAL(4,2) | Hz | 0-10 | Band valid end freq |
| 7 | Hm0 | float | DECIMAL(5,2) | m | 0-100 | Sig wave height in band |
| 8 | Tm02 | float | DECIMAL(5,2) | s | 0-100 | Mean period in band |
| 9 | Tp | float | DECIMAL(5,2) | s | 0-100 | Peak period in band |
| 10 | DirTp | float | DECIMAL(5,2) | deg | 0-360 | Peak direction in band |
| 11 | SprTp | float | DECIMAL(5,2) | deg | 0-360 | Dir spread in band |
| 12 | MainDir | float | DECIMAL(5,2) | deg | 0-360 | Mean direction in band |
| 13 | Error Code | str | CHAR(4) | - | - | Error code |

## Example Sentence

```
$PNORB,102115,090715,0,1,0.05,0.50,1.20,6.50,7.20,285.0,20.0,280.0,0000*XX
```

**Parsed**:
- Date: 10/21/15, Time: 09:07:15
- Band: 0.05-0.50 Hz
- Hm0: 1.20m in band
- Tp: 7.20s in band
- DirTp: 285.0° in band

## Related Documents

- [PNORW - General Wave Data](../pnorw/pnorw.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
