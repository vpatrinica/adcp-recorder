[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORI Family](README.md)

# PNORI2 Specification

**Tagged instrument information** (DF=102) with configuration parameters.

## Format

```nmea
$PNORI2,IT=InstrType,SN=HeadID,NB=BeamCnt,NC=CellCnt,BD=BlankDist,CS=CellSize,CY=CoordSys*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|-----|-------|-------------|-------------|------|--------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | "$PNORI2" | - | Always `$PNORI2` |
| IT | Instrument Type | int | TINYINT | - | N | 0,2,4 | 0=Aquadopp, 2=Profiler, 4=Signature |
| SN | Serial Number | str | VARCHAR(20) | - | N | - | Head ID (numeric) |
| NB | Number of Beams | int | TINYINT | - | N | 1-4 | Acoustic beam count |
| NC | Number of Cells | int | SMALLINT | - | N | 1-1000 | Measurement cell count |
| BD | Blanking Distance | float | DECIMAL(5,2) | m | dd.dd | 0-99 | Distance to first cell |
| CS | Cell Size | float | DECIMAL(5,2) | m | dd.dd | 0-99 | Size of each cell |
| CY | Coordinate System | str | VARCHAR(4) | - | N | - | ENU, XYZ, or BEAM |

## Instrument Types

| Value | Name | Description |
|-------|------|-------------|
| 0 | Aquadopp | Single-point current meter |
| 2 | Aquadopp Profiler | profiling ADCP |
| 4 | Signature | Multi-beam profiler |

## Example Sentence

```nmea
$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68
```

**Parsed**:

- Instrument Type (IT): 4 (Signature)
- Serial Number (SN): 123456
- Number of Beams (NB): 4
- Number of Cells (NC): 30
- Blanking Distance (BD): 1.00 m
- Cell Size (CS): 5.00 m
- Coordinate System (CY): BEAM

## Related Documents

- [PNORI1](pnori1.md) - Same data, positional format
- [PNORI Family Overview](README.md)

---

[⬆️ Back to PNORI Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
