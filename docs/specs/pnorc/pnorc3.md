[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORC Family](README.md)

# PNORC3 Specification

**Tagged averaged current data** (DF=103) containing cell-averaged velocity measurements.

## Format

```nmea
$PNORC3,CP=CellPos,SP=Speed,DIR=Direction,AC=AvgCorr,AA=AvgAmp*CHECKSUM
```

**Field Count**: 6 fields (prefix + 5 tagged values)

## Field Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|-----|-------|-------------|-------------|------|--------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | "$PNORC3" | - | Always `$PNORC3` |
| CP | Cell Position | float | DECIMAL(5,1) | m | dd.d | 0-999 | Distance to cell center |
| SP | Speed | float | DECIMAL(6,3) | m/s | dd.ddd | 0-99 | Current speed magnitude |
| DIR | Direction | float | DECIMAL(5,1) | deg | ddd.d | 0-360 | Current direction |
| AC | Avg Correlation | int | TINYINT | - | N | 0-100 | Averaged correlation |
| AA | Avg Amplitude | int | TINYINT | - | N | 0-255 | Averaged amplitude |

## Example Sentence

```nmea
$PNORC3,CP=4.5,SP=3.519,DIR=110.9,AC=6,AA=28*3B
```

**Parsed**:

- Cell Position: 4.5 m from transducer
- Speed: 3.519 m/s
- Direction: 110.9° (from ENE)
- Avg Correlation: 6
- Avg Amplitude: 28

## Differences from PNORC/PNORC4

- **Format**: Tagged (TAG=VALUE) vs positional
- **Data**: Averaged values per cell, not per-beam raw data
- **Use**: Compact reporting with self-describing tags

## Related Documents

- [PNORC Family Overview](README.md)
- [PNORC4](pnorc4.md) - Same data, positional format

---

[⬆️ Back to PNORC Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
