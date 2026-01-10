[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORI Family](README.md)

# PNORI2 Specification

**Tagged instrument configuration message** with TAG=VALUE pairs for Flexible field ordering.

## Format

```
$PNORI2,IT=InstrType,SN=HeadID,NB=BeamCnt,NC=CellCnt,BD=BlankDist,CS=CellSize,CY=CoordSys*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

**Differences from PNORI/PNORI1**:
- Uses **TAG=VALUE** format instead of positional fields
- Field order is **not significant**
- Coordinate system is a string (like PNORI1)

## Tag Definitions

| Tag | Field | Python Type | DuckDB Type | Unit | Range | Description |
|-----|-------|-------------|-------------|------|-------|-------------|
| - | Prefix | str | VARCHAR(10) | - | - | Always `$PNORI2` |
| IT | Instrument Type | int | TINYINT | - | 0, 2, 4 | 0=Aquadopp, 2=Aquadopp Profiler, 4=Signature |
| SN | Serial Number | str | VARCHAR(20) | - | 1-20 chars | Instrument serial number |
| NB | Number of Beams | int | TINYINT | beams | 1-4 | Number of acoustic beams |
| NC | Number of Cells | int | SMALLINT | cells | 1-1000 | Number of measurement cells |
| BD | Blanking Distance | float | DECIMAL(5,2) | meters | 0.01-100.0 | Distance in meters |
| CS | Cell Size | float | DECIMAL(5,2) | meters | 0.01-100.0 | Size in meters |
| CY | Coordinate System | str | VARCHAR(10) | - | - | String: ENU, XYZ, or BEAM |

## Example Sentence

```
$PNORI2,IT=4,SN=123456,NB=4,NC=30,BD=1.00,CS=5.00,CY=BEAM*68
```

**Parsed**:
- Instrument Type (IT): 4 (Signature)
- Serial Number (SN): `123456`
- Number of Beams (NB): 4
- Number of Cells (NC): 30
- Blanking Distance (BD): 1.00 m
- Cell Size (CS): 5.00 m
- Coordinate System (CY): BEAM
- Checksum: `68`

## Python Data Structure

```python
from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Optional, ClassVar, Dict
import re

class PNORTag:
    """Tag definitions for PNORI2 format."""
    INSTRUMENT_TYPE = "IT"
    SERIAL_NUMBER = "SN"
    NUM_BEAMS = "NB"
    NUM_CELLS = "NC"
    BLANKING_DISTANCE = "BD"
    CELL_SIZE = "CS"
    COORDINATE_SYSTEM = "CY"
    
    VALID_TAGS = {INSTRUMENT_TYPE, SERIAL_NUMBER, NUM_BEAMS, NUM_CELLS,
                  BLANKING_DISTANCE, CELL_SIZE, COORDINATE_SYSTEM}
    
    @classmethod
    def parse_tagged_field(cls, field: str) -> tuple[str, str]:
        if '=' not in field:
            raise ValueError(f"Tagged field must contain '=': {field}")
        
        tag, value = field.split('=', 1)
        tag = tag.strip().upper()
        
        if tag not in cls.VALID_TAGS:
            raise ValueError(f"Unknown tag: {tag}")
        
        return tag, value.strip()

@dataclass(frozen=True)
class PNORI2:
    instrument_type: InstrumentType
    head_id: str
    beam_count: int
    cell_count: int
    blanking_distance: float
    cell_size: float
    coordinate_system: CoordinateSystem
    checksum: Optional[str] = field(default=None, repr=False)
    
    @classmethod
    def from_sentence(cls, sentence: str) -> 'PNORI2':
        sentence = sentence.strip()
        
        if '*' in sentence:
            data_part, checksum = sentence.rsplit('*', 1)
            checksum = checksum.strip().upper()
        else:
            data_part, checksum = sentence, None
        
        fields = [f.strip() for f in data_part.split(',')]
        
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields, got {len(fields)}")
        
        if fields[0] != "$PNORI2":
            raise ValueError(f"Invalid identifier: {fields[0]}")
        
        # Parse tagged fields
        data = {}
        for field in fields[1:]:
            tag, value = PNORTag.parse_tagged_field(field)
            data[tag] = value
        
        # Verify all required tags present
        if set(data.keys()) != PNORTag.VALID_TAGS:
            missing = PNORTag.VALID_TAGS - set(data.keys())
            raise ValueError(f"Missing required tags: {missing}")
        
        return cls(
            instrument_type=InstrumentType(int(data[PNORTag.INSTRUMENT_TYPE])),
            head_id=data[PNORTag. SERIAL_NUMBER],
            beam_count=int(data[PNORTag.NUM_BEAMS]),
            cell_count=int(data[PNORTag.NUM_CELLS]),
            blanking_distance=float(data[PNORTag.BLANKING_DISTANCE]),
            cell_size=float(data[PNORTag.CELL_SIZE]),
            coordinate_system=CoordinateSystem(data[PNORTag.COORDINATE_SYSTEM]),
            checksum=checksum
        )
```

## DuckDB Schema

Shares the same `pnori_configurations` table with PNORI and PNORI1:

```sql
-- sentence_type will be 'PNORI2'
-- Fields are mapped from TAG=VALUE pairs
```

## Validation Rules

Same as [PNORI1](pnori1.md), with additional rules:

8. **Required Tags**: All 7 tags (IT, SN, NB, NC, BD, CS, CY) must be present
9. **Tag Format**: Each field must contain exactly one '=' character
10. **Unknown Tags**: Any tag not in the valid set is rejected

## Parsing Advantages

**PNORI2 advantages**:
- Order-independent: Tags can appear in any sequence
- Self-documenting: Field names are explicit
- Extensible: New tags can be added without breaking compatibility

**Trade-offs**:
- Longer sentences (more bytes transmitted)
- Slightly more complex parsing

## Related Documents

- [PNORI Family Overview](README.md)
- [PNORI Specification](pnori.md)
- [PNORI1 Specification](pnori1.md)

---

[⬆️ Back to PNORI Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
