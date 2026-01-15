[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORI Family](README.md)

# PNORI Specification

**Positional instrument configuration** (DF=100) with numeric coordinate system code.

## Format

```nmea
$PNORI,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Format | Range | Description |
|----------|-------|-------------|-------------|------|--------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | "$PNORI" | - | Always `$PNORI` |
| 1 | Instrument Type | int | TINYINT | - | N | 0,2,4 | 0=Aquadopp, 2=Profiler, 4=Signature |
| 2 | Head ID | str | VARCHAR(30) | - | String | 1-30 chars | Serial number (alphanumeric) |
| 3 | Number of Beams | int | TINYINT | - | N | 1-4 | Acoustic beam count |
| 4 | Number of Cells | int | SMALLINT | - | N | 1-1000 | Measurement cell count |
| 5 | Blanking Distance | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Distance to first cell |
| 6 | Cell Size | float | DECIMAL(5,2) | m | dd.dd | 0-99.99 | Size of each cell |
| 7 | Coordinate System | int | TINYINT | - | N | 0,1,2 | 0=ENU, 1=XYZ, 2=BEAM |

## Instrument Types

| Value | Name | Description |
|-------|------|-------------|
| 0 | Aquadopp | Single-point current meter |
| 2 | Aquadopp Profiler | profiling ADCP |
| 4 | Signature | Multi-beam profiler |

## Coordinate Systems

| Value | Name | Description |
|-------|------|-------------|
| 0 | ENU | East-North-Up (geographic) |
| 1 | XYZ | Instrument frame |
| 2 | BEAM | Along-beam velocities |

## Example Sentence

```nmea
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
```

**Parsed**:

- Instrument Type: 4 (Signature)
- Head ID: Signature1000900001
- Number of Beams: 4
- Number of Cells: 20
- Blanking Distance: 0.20 m
- Cell Size: 1.00 m
- Coordinate System: 0 (ENU)

## Related Documents

- [PNORI1](pnori1.md) - Same data, string coordinate system
- [PNORI2](pnori2.md) - Same data, tagged format
- [PNORI Family Overview](README.md)

---

[⬆️ Back to PNORI Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
