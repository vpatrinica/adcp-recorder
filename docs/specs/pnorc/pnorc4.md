[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC4 Specification

**Positional averaged current data** (DF=104) containing cell-averaged velocity measurements.

## Format

```nmea
$PNORC4,CellPos,Speed,Direction,AvgCorr,AvgAmp*CHECKSUM
```

**Field Count**: 6 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORC4" | - | Always `$PNORC4` |
| 1 | Cell Position | float | DECIMAL(5,1) | m | dd.d | 0-999 | Distance to cell center |
| 2 | Speed | float | DECIMAL(6,3) | m/s | dd.ddd | 0-99 | Current speed magnitude |
| 3 | Direction | float | DECIMAL(5,1) | deg | ddd.d | 0-360 | Current direction |
| 4 | Avg Correlation | int | TINYINT | - | N | 0-100 | Averaged correlation |
| 5 | Avg Amplitude | int | TINYINT | - | N | 0-255 | Averaged amplitude |

## Example Sentence

```nmea
$PNORC4,27.5,1.815,322.6,4,28*70
```

**Parsed**:

- Cell Position: 27.5 m from transducer
- Speed: 1.815 m/s
- Direction: 322.6° (from NW)
- Avg Correlation: 4
- Avg Amplitude: 28

## Differences from PNORC3

- **Format**: Positional (fixed order) vs tagged (TAG=VALUE)
- **Use**: Compact binary-efficient format
- **Data**: Identical fields and meanings

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC3](pnorc3.md) - Same data, tagged format

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
