[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORI Family](README.md)

# PNORI1 Specification

**Positional instrument information** (DF=101) with configuration parameters.

## Format

```nmea
$PNORI1,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORI1" | - | Always `$PNORI1` |
| 1 | Instrument Type | int | TINYINT | - | N | 0,2,4 | 0=Aquadopp, 2=Aquadopp Profiler, 4=Signature |
| 2 | Head ID | str | VARCHAR(20) | - | N | - | Serial number (numeric) |
| 3 | Number of Beams | int | TINYINT | - | N | 1-4 | Acoustic beam count |
| 4 | Number of Cells | int | SMALLINT | - | N | 1-1000 | Measurement cell count |
| 5 | Blanking Distance | float | DECIMAL(5,2) | m | dd.dd | 0-99 | Distance to first cell |
| 6 | Cell Size | float | DECIMAL(5,2) | m | dd.dd | 0-99 | Size of each cell |
| 7 | Coordinate System | str | VARCHAR(4) | - | N | - | ENU, XYZ, or BEAM |

## Instrument Types

| Value | Name | Description |
|-------|------|-------------|
| 0 | Aquadopp | Single-point current meter |
| 2 | Aquadopp Profiler | profiling ADCP |
| 4 | Signature | Multi-beam profiler |

## Example Sentence

```nmea
$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B
```

**Parsed**:

- Instrument Type: 4 (Signature)
- Head ID: 123456
- Number of Beams: 4
- Number of Cells: 30
- Blanking Distance: 1.00 m
- Cell Size: 5.00 m
- Coordinate System: BEAM

## Related Documents

- [PNORI2](pnori2.md) - Same data, tagged format
- [PNORI Family Overview](README.md)

---

[⬆️ Back to PNORI Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
