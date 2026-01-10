[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORI Family](README.md)

# PNORI Specification

**Base instrument configuration message** with positional fields and numeric coordinate system code.

## Format

```
$PNORI,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORI` |
| 1 | Instrument Type | int | TINYINT | - | 0, 2, 4 | 0=Aquadopp, 2=Aquadopp Profiler, 4=Signature |
| 2 | Head ID | str | VARCHAR(30) | - | 1-30 chars | Serial number or instrument identifier |
| 3 | Beam Count | int | TINYINT | beams | 1-4 | Number of acoustic beams |
| 4 | Cell Count | int | SMALLINT | cells | 1-1000 | Number of measurement cells |
| 5 | Blanking Distance | float | DECIMAL(5,2) | meters | 0.01-100.0 | Distance to first measurement |
| 6 | Cell Size | float | DECIMAL(5,2) | meters | 0.01-100.0 | Size of each measurement cell |
| 7 | Coordinate System | int | TINYINT | - | 0, 1, 2 | 0=ENU, 1=XYZ, 2=BEAM |

## Example Sentence

```
$PNORI,4,Signature1000900001,4,20,0.20,1.00,0*2E
```

**Parsed**:
- Instrument Type: 4 (Signature)
- Head ID: `Signature1000900001`
- Beam Count: 4
- Cell Count: 20
- Blanking Distance: 0.20 m
- Cell Size: 1.00 m
- Coordinate System: 0 (ENU)
- Checksum: `2E`

## Python Data Structure

```python
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, ClassVar
import re

class InstrumentType(IntEnum):
    AQUADOPP = 0
    AQUADOPP_PROFILER = 2
    SIGNATURE = 4

class CoordinateSystem(IntEnum):
    ENU = 0
    XYZ = 1
    BEAM = 2

@dataclass(frozen=True)
class PNORI:
    instrument_type: InstrumentType
    head_id: str
    beam_count: int
    cell_count: int
    blanking_distance: float
    cell_size: float
    coordinate_system: CoordinateSystem
    checksum: Optional[str] = field(default=None, repr=False)
    
    HEAD_ID_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[A-Za-z0-9\s]{1,30}$')
    
    def __post_init__(self):
        self._validate_head_id()
        self._validate_beam_count()
        self._validate_cell_count()
        self._validate_distances()
        
    @classmethod
    def from_nmea(cls, sentence: str) -> 'PNORI':
        sentence = sentence.strip()
        
        if '*' in sentence:
            data_part, checksum = sentence.rsplit('*', 1)
            checksum = checksum.strip().upper()
        else:
            data_part, checksum = sentence, None
        
        fields = [f.strip() for f in data_part.split(',')]
        
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields, got {len(fields)}")
        
        if fields[0] != "$PNORI":
            raise ValueError(f"Invalid identifier: {fields[0]}")
        
        return cls(
            instrument_type=InstrumentType(int(fields[1])),
            head_id=fields[2],
            beam_count=int(fields[3]),
            cell_count=int(fields[4]),
            blanking_distance=float(fields[5]),
            cell_size=float(fields[6]),
            coordinate_system=CoordinateSystem(int(fields[7])),
            checksum=checksum
        )
```

## DuckDB Schema

```sql
CREATE TABLE pnori_configurations (
    config_id UUID PRIMARY KEY DEFAULT uuid(),
    
    -- Sentence metadata
    sentence_type VARCHAR(10) DEFAULT 'PNORI',
    original_sentence TEXT NOT NULL,
    
    -- Configuration fields
    instrument_type_name VARCHAR(20) NOT NULL,
    instrument_type_code TINYINT NOT NULL 
        CHECK (instrument_type_code IN (0, 2, 4)),
    head_id VARCHAR(30) NOT NULL 
        CHECK (length(head_id) BETWEEN 1 AND 30),
    beam_count TINYINT NOT NULL 
        CHECK (beam_count > 0 AND beam_count <= 4),
    cell_count SMALLINT NOT NULL 
        CHECK (cell_count > 0 AND cell_count <= 1000),
    blanking_distance DECIMAL(5,2) NOT NULL 
        CHECK (blanking_distance > 0 AND blanking_distance <= 100),
    cell_size DECIMAL(5,2) NOT NULL 
        CHECK (cell_size > 0 AND cell_size <= 100),
    coord_system_name VARCHAR(10) NOT NULL 
        CHECK (coord_system_name IN ('ENU', 'XYZ', 'BEAM')),
    coord_system_code TINYINT NOT NULL 
        CHECK (coord_system_code IN (0, 1, 2)),
    
    -- Metadata
    checksum CHAR(2),
    parsed_at TIMESTAMP DEFAULT current_timestamp,
    
    -- Cross-field validation
    CONSTRAINT valid_signature_config CHECK (
        NOT (instrument_type_code = 4 AND beam_count != 4)
    ),
    CONSTRAINT valid_coord_mapping CHECK (
        (coord_system_name = 'ENU' AND coord_system_code = 0) OR
        (coord_system_name = 'XYZ' AND coord_system_code = 1) OR
        (coord_system_name = 'BEAM' AND coord_system_code = 2)
    )
);

CREATE INDEX idx_pnori_head_id ON pnori_configurations(head_id);
```

## Validation Rules

1. **Instrument Type**: Must be 0, 2, or 4
2. **Head ID**: Alphanumeric, 1-30 characters
3. **Signature Beams**: If type=4, beam_count must be 4
4. **Aquadopp Beams**: If type in (0,2), beam_count must be 1, 2, or 3
5. **Cell Count**: 1 to 1000
6. **Blanking Distance**: Positive, ≤ 100 m
7. **Cell Size**: Positive, ≤ 100 m
8. **Coordinate System**: Must be 0, 1, or 2

## Related Documents

- [PNORI Family Overview](README.md)
- [PNORI1 Specification](pnori1.md)
- [PNORI2 Specification](pnori2.md)

---

[⬆️ Back to PNORI Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
