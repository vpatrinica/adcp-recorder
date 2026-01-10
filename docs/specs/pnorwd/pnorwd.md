[🏠 Home](../../README.md) > [📋 Specs](../README.md)

# PNORWD Specification

**Wave directional data message** with directional wave spectrum information.

## Format

```
$PNORWD,MMDDYY,HHMMSS,FreqBin,Direction,SpreadAngle,Energy*CHECKSUM
```

**Field Count**: 7 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORWD` |
| 1 | Date | str | CHAR(6) | - | MMDDYY | Measurement date |
| 2 | Time | str | CHAR(6) | - | HHMMSS | Measurement time |
| 3 | Frequency Bin | int | TINYINT | - | 1-100 | Frequency bin index |
| 4 | Direction | float | DECIMAL(5,1) | degrees | 0-360 | Wave propagation direction |
| 5 | Directional Spread | float | DECIMAL(5,1) | degrees | 0-180 | Angular spread of wave energy |
| 6 | Spectral Energy | float | DECIMAL(8,4) | m²/Hz | 0-100 | Energy density at this frequency |

## Example Sentence

```
$PNORWD,102115,090715,5,280.5,25.0,1.25*XX
```

**Parsed**:
- Date: October 21, 2015
- Time: 09:07:15
- Frequency Bin: 5
- Direction: 280.5° (from WNW)
- Directional Spread: 25.0°
- Spectral Energy: 1.25 m²/Hz

## Usage

Directional wave spectrum data provides:
- Frequency-dependent wave directions
- Directional spreading characteristics
- Full 2D wave spectrum reconstruction
- Advanced wave climate analysis

## Related Documents

- [PNORW - Wave Data](../pnorw/pnorw.md)
- [All Specifications](../README.md)

---

[📋 All Specs](../README.md) | [🏠 Home](../../README.md)
