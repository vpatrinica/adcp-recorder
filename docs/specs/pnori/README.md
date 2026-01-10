[🏠 Home](../../README.md) > [📋 Specs](../README.md) > PNORI Family

# PNORI Message Family

The PNORI family contains instrument configuration messages that describe the physical setup and operating parameters of Nortek ADCP instruments.

## Message Variants

- **[PNORI](pnori.md)** - Base configuration format (positional fields, numeric coordinate system)
- **[PNORI1](pnori1.md)** - Untagged configuration format (positional fields, string coordinate system)
- **[PNORI2](pnori2.md)** - Tagged configuration format (TAG=VALUE pairs)

## Common Fields

All PNORI variants contain these configuration parameters:

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| Instrument TypeInstrumentType(IntEnum) | - | Instrument model (0=Aquadopp, 2=Aquadopp Profiler, 4=Signature) |
| Head ID / Serial Number | String | - | Instrument serial number or identifier |
| Beam Count | Integer | beams | Number of acoustic beams (1-4) |
| Cell Count | Integer | cells | Number of measurement cells/bins |
| Blanking Distance | Float | meters | Distance from transducer to first measurement |
| Cell Size | Float | meters | Size of each measurement cell |
| Coordinate System | Enum | - | Velocity coordinate system (ENU/XYZ/BEAM) |

## Instrument Types

```python
class InstrumentType(IntEnum):
    AQUADOPP = 0          # Single-point current meter
    AQUADOPP_PROFILER = 2 # Profiling current meter
    SIGNATURE = 4         # High-performance ADCP
```

### Beam Constraints

- **Signature (type 4)**: Must have exactly **4 beams**
- **Aquadopp (types 0, 2)**: Can have **1-3 beams**

## Coordinate Systems

```python
class CoordinateSystem:
    ENU = 0   # East-North-Up (geographic coordinates)
    XYZ = 1   # Instrument XYZ (instrument-fixed coordinates)
    BEAM = 2  # Raw beam coordinates
```

### Coordinate System Usage

- **ENU**: Geographically-oriented velocities (requires compass)
- **XYZ**: Instrument-fixed coordinates (no compass needed)
- **BEAM**: Raw beam velocities (for advanced processing)

## Format Comparison

### PNORI (Base)
```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
       │ │                  │ │  │    │    └─ Coord system (numeric)
       │ │                  │ │  │    └─ Cell size
       │ │                  │ │  └─ Blanking distance
       │ │                  │ └─ Cell count
       │ │                  └─ Beam count
       │ └─ Head ID
       └─ Instrument type
```

### PNORI1 (Untagged)
```
$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B
        │ │      │ │  │    │    └─ Coord system (string)
        │ │      │ │  │    └─ Cell size
        │ │      │ │  └─ Blanking distance
        │ │      │ └─ Cell count
        │ │      └─ Beam count
        │ └─ Head ID
        └─ Instrument type
```

### PNORI2 (Tagged)
```
$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68
        │    │         │    │     │       │       └─ Coordinate system
        │    │         │    │     │       └─ Cell size
        │    │         │    │     └─ Blanking distance
        │    │         │    └─ Cell count (Number of Cells)
        │    │         └─ Beam count (Number of Beams)
        │    └─ Serial Number
        └─ Instrument Type
```

## Tag Definitions (PNORI2)

| Tag | Field | Description |
|-----|-------|-------------|
| IT | Instrument Type | Numeric code (0, 2, or 4) |
| SN | Serial Number | Instrument serial number |
| NB | Number of Beams | Beam count (1-4) |
| NC | Number of Cells | Cell count (1-1000) |
| BD | Blanking Distance | Distance in meters |
| CS | Cell Size | Size in meters |
| CY | Coordinate System | String: ENU, XYZ, or BEAM |

## Validation Rules

### Field Constraints

1. **Instrument Type**: Must be 0, 2, or 4
2. **Head ID**: 1-30 alphanumeric characters
3. **Beam Count**: 1-4 beams
4. **Cell Count**: 1-1000 cells
5. **Blanking Distance**: 0.01-100.0 meters
6. **Cell Size**: 0.01-100.0 meters
7. **Coordinate System**: 0-2 (or ENU/XYZ/BEAM)

### Cross-Field Validation

1. **Signature beams**: If instrument_type==4, then beam_count must == 4
2. **Aquadopp beams**: If instrument_type in (0,2), then beam_count in (1,2,3)
3. **Blanking vs. cells**: blanking_distance < (cell_size * cell_count)

## Usage Context

Configuration messages are typically:
- Sent once at instrument startup
- Logged at the beginning of a deployment
- Used to interpret subsequent velocity data (PNORC) and sensor data (PNORS)

**Important**: Configuration parameters must be known to correctly interpret velocity measurements.

## DuckDB Storage

All PNORI variants are stored in a unified table:

```sql
CREATE TABLE pnori_configurations (
    config_id UUID PRIMARY KEY DEFAULT uuid(),
    sentence_type VARCHAR(10) NOT NULL,  -- 'PNORI', 'PNORI1', or 'PNORI2'
    instrument_type_name VARCHAR NOT NULL,    instrument_type_code TINYINT NOT NULL,
    head_id VARCHAR NOT NULL,
    beam_count TINYINT NOT NULL,
    cell_count SMALLINT NOT NULL,
    blanking_distance DECIMAL(5,2) NOT NULL,
    cell_size DECIMAL(5,2) NOT NULL,
    coord_system_name VARCHAR NOT NULL,
    coord_system_code TINYINT NOT NULL,
    checksum CHAR(2),
    parsed_at TIMESTAMP DEFAULT current_timestamp
);
```

## Example Sentences

```python
# PNORI (Base)
"$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E"

# PNORI1 (Untagged)
"$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B"

# PNORI2 (Tagged)
"$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68"
```

## Related Documents

- [PNORI Base Specification](pnori.md)
- [PNORI1 Specification](pnori1.md)
- [PNORI2 Specification](pnori2.md)
- [Python Parser Implementation](../../implementation/python/parsers.md)
- [DuckDB Schema](../../implementation/duckdb/schemas.md)

---

[⬆️ Back to Specifications](../README.md) | [🏠 Home](../../README.md)
