# Parser Development Guide

## How to Add a New Parser

### 1. Create the parser file

Create `adcp_recorder/parsers/pnorx.py`:

```python
"""PNORX <description> parser."""

from dataclasses import dataclass, field
from typing import Any, cast

from .utils import (
    parse_nmea_sentence,
    parse_optional_float,
    validate_date_mm_dd_yy,  # or validate_date_yy_mm_dd
    validate_range,
    validate_time_string,
)


@dataclass(frozen=True)
class PNORX:
    """PNORX <description>.
    Format: $PNORX,field1,field2,...*CS
    """
    
    date: str
    time: str
    # ... your fields
    is_valid: bool = True
    checksum: str | None = field(default=None, repr=False)
    
    def __post_init__(self):
        validate_date_mm_dd_yy(self.date)
        validate_time_string(self.time)
        # Add any field-specific validation
    
    @classmethod
    def from_nmea(cls, sentence: str) -> "PNORX":
        res = parse_nmea_sentence(sentence)
        fields, checksum = cast(list[str], res[0]), cast(str | None, res[1])
        
        if fields[0] != "$PNORX":
            raise ValueError(f"Invalid prefix: {fields[0]}")
        
        if len(fields) < EXPECTED_FIELD_COUNT:
            raise ValueError(f"Expected {EXPECTED_FIELD_COUNT} fields, got {len(fields)}")
        
        return cls(
            date=fields[1],
            time=fields[2],
            # ... parse remaining fields
            checksum=checksum,
        )
    
    def to_dict(self) -> dict:
        return {
            "sentence_type": "PNORX",
            "date": self.date,
            "time": self.time,
            # ... all fields
            "checksum": self.checksum,
        }
```

### 2. Register in `__init__.py`

Add your class to `adcp_recorder/parsers/__init__.py`.

### 3. Write tests

Create `adcp_recorder/tests/parsers/test_pnorx.py`. See existing tests for patterns.

**Important test rules:**
- Always compute correct checksums for test sentences (use `fix_tests.py`)
- For f-strings with dynamic values, **omit the checksum** — it can't be pre-computed
- For sentences testing invalid prefixes, **omit the checksum** — checksum validation fires first
- Test NaN handling: `"nan"`, `"-nan"` → `None`

## Shared Utilities (utils.py)

| Function | Purpose |
|----------|---------|
| `parse_nmea_sentence(sentence)` | Split into fields + validate checksum |
| `parse_optional_float(value)` | Parse float, return `None` for NaN/empty |
| `parse_optional_int(value)` | Parse int, return `None` for NaN/empty |
| `is_nan_string(value)` | Check if string is NaN (`"nan"`, `"-nan"`, case-insensitive) |
| `parse_tagged_field(field)` | Parse `TAG=VALUE` format |
| `validate_date_mm_dd_yy(date)` | Validate MMDDYY format |
| `validate_date_yy_mm_dd(date)` | Validate YYMMDD format |
| `validate_time_string(time)` | Validate HHMMSS format |
| `validate_hex_string(hex)` | Validate hex string |
| `validate_range(val, name, min, max)` | Validate numeric range |

## Parser Formats

### Positional Parsers (DF=100/200/etc.)
Fields are comma-separated in a fixed order:
```
$PNORB,102115,090715,1,4,0.02,0.20,0.27,7.54,12.00,82.42,75.46,82.10,0000*63
```

### Tagged Parsers (DF=101/201/etc.)
Fields use `TAG=VALUE` format, order-independent:
```
$PNORI2,IT=4,SN=Sig1000,NB=4,NC=20,BD=0.20,CS=1.00,CY=ENU
```

### Variable-Length Parsers
Some parsers (PNORE, PNORF, PNORWD) have variable-length arrays:
```
$PNORE,120720,093150,1,0.02,0.01,10,E1,E2,...,E10*CS
```
The `num_frequencies` field tells how many values follow.
