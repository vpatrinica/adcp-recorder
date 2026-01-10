[🏠 Home](../../README.md) > [📋 Specs](../README.md) > [PNORI Family](README.md)

# PNORI1 Specification

**Untagged instrument configuration message** with positional fields and string coordinate system.

## Format

```
$PNORI1,InstrType,HeadID,BeamCnt,CellCnt,BlankDist,CellSize,CoordSys*CHECKSUM
```

**Field Count**: 8 fields (including prefix)

**Differences from PNORI**:
- Coordinate system is a **string** (ENU/XYZ/BEAM) instead of numeric code
- Otherwise identical structure

## Field Definitions

| Position | Field | Python Type | DuckDB Type | Unit | Range | Description |
|----------|-------|-------------|-------------|------|-------|-------------|
| 0 | Prefix | str | VARCHAR(10) | - | - | Always `$PNORI1` |
| 1 | Instrument Type | int | TINYINT | - | 0, 2, 4 | 0=Aquadopp, 2=Aquadopp Profiler, 4=Signature |
| 2 | Head ID | str | VARCHAR(20) | - | 1-20 chars | Serial number or instrument identifier |
| 3 | Beam Count | int | TINYINT | beams | 1-4 | Number of acoustic beams |
| 4 | Cell Count | int | SMALLINT | cells | 1-1000 | Number of measurement cells |
| 5 | Blanking Distance | float | DECIMAL(5,2) | meters | 0.01-100.0 | Distance to first measurement |
| 6 | Cell Size | float | DECIMAL(5,2) | meters | 0.01-100.0 | Size of each measurement cell |
| 7 | Coordinate System | str | VARCHAR(10) | - | - | ENU, XYZ, or BEAM |

## Example Sentence

```
$PNORI1,4,123456,4,30,1.00,5.00,BEAM*5B
```

**Parsed**:
- Instrument Type: 4 (Signature)
- Head ID: `123456`
- Beam Count: 4
- Cell Count: 30
- Blanking Distance: 1.00 m
- Cell Size: 5.00 m
- Coordinate System: BEAM
- Checksum: `5B`

## Python Data Structure

```python
from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Optional, ClassVar
import re

class InstrumentType(IntEnum):
    AQUADOPP = 0
    AQUADOPP_PROFILER = 2
    SIGNATURE = 4

class CoordinateSystem(Enum):
    ENU = "ENU"
    XYZ = "XYZ"
    BEAM = "BEAM"
    
    def to_numeric_code(self) -> int:
        mapping = {self.ENU: 0, self.XYZ: 1, self.BEAM: 2}
        return mapping[self]

@dataclass(frozen=True)
class PNORI1:
    instrument_type: InstrumentType
    head_id: str
    beam_count: int
    cell_count: int
    blanking_distance: float
    cell_size: float
    coordinate_system: CoordinateSystem
    checksum: Optional[str] = field(default=None, repr=False)
    
    HEAD_ID_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[A-Za-z0-9]{1,20}$')
    
    @classmethod
    def from_sentence(cls, sentence: str) -> 'PNORI1':
        sentence = sentence.strip()
        
        if '*' in sentence:
            data_part, checksum = sentence.rsplit('*', 1)
            checksum = checksum.strip().upper()
        else:
            data_part, checksum = sentence, None
        
        fields = [f.strip() for f in data_part.split(',')]
        
        if len(fields) != 8:
            raise ValueError(f"Expected 8 fields, got {len(fields)}")
        
        if fields[0] != "$PNORI1":
            raise ValueError(f"Invalid identifier: {fields[0]}")
        
        return cls(
            instrument_type=InstrumentType(int(fields[1])),
            head_id=fields[2],
            beam_count=int(fields[3]),
            cell_count=int(fields[4]),
            blanking_distance=float(fields[5]),
            cell_size=float(fields[6]),
            coordinate_system=CoordinateSystem(fields[7]),
            checksum=checksum
        )
```

## DuckDB Schema

Shares the same `pnori_configurations` table with PNORI and PNORI2:

```sql
-- sentence_type will be 'PNORI1'
-- coord_system_name will be string value ('ENU', 'XYZ', 'BEAM')
-- coord_system_code will be mapped numeric value (0, 1, 2)
```

## Validation Rules

Same as [PNORI](pnori.md) with additional rule:

7. **Coordinate System**: Must be exactly "ENU", "XYZ", or "BEAM" (case-sensitive)

## Related Documents

- [PNORI Family Overview](README.md)
- [PNORI Specification](pnori.md)
- [PNORI2 Specification](pnori2.md)

---

[⬆️ Back to PNORI Family](README.md) | [📋 All Specs](../README.md) | [🏠 Home](../../README.md)
